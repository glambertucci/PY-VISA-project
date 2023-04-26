import pyvisa as visa
import logging
import time
import numpy as np
from Source import Resources
import matplotlib.pyplot as plt
import os
import csv
import cmath

OSC_RESOURC = 0
GEN_RESOURC = 1

FIRST_CHANNEL = 0
SECOND_CHANNEL = 1
MATH_SOURCE_1 = 2
MATH_SOURCE_2 = 3

STARTING_DIV_VAL = 0.001
HFREJECT_CUTOFF = 5*10**4
HIGH_RES_CUTOFF = 1*10**5

EASTER = 'guidin'
IMPEDANCE = 'Z'
BODE = 'B'
EXIT = 'E'
TRAN = 'T'

class Measurer():
    def __init__(self):
        self.chan1 = 1          #Primer canal de medicion
        self.chan2 = 1          #Segundo canal de medicion
        self.f = []             #Frecuencias a evaluar
        self.voltage = 0        #Tension del generador a usar
        self.frequency = 0      #Frecuencia del generador a usar
        self.openResources=[]   #Recursos abiertos
        logging.info("Creando resource manager.")
        #self.resourceManager = visa.ResourceManager('@sim') #Para simular un instrumento
        self.resourceManager = visa.ResourceManager()
        if(len(self.resourceManager.list_resources()) != 0): #Me fijo si hay instrumentos disponibles
            print("Conectarse al osciloscopio.")
            if(self.connect(OSC_RESOURC)):          #Se realiza la coneccion al osciloscopio
                pass
                print("Conectar el generador de funciones.")
                if(self.connect(GEN_RESOURC)):      #Se realiza la coneccion al generador de funciones

                    user_exit = False
                    while(not user_exit):
                        measurement = self.ask_which_measurement()
                        if(measurement == EXIT):
                            user_exit = True
                        elif(measurement == BODE):
                            self.bode()  # Se realiza la medicion de bode
                        elif(measurement == IMPEDANCE):
                            self.impedance_meas=True
                            self.bode()  # Se realiza la medicion de bode teniendo en cuenta que se mide una corriente
                            self.impedance_meas=False
                        elif(measurement == EASTER):
                            print("Ay che.")
                else:
                    print("Error con el generador de funciones.")
            else:
                print("Error con el osciloscopio.")
        else:
            print("No hay instrumentos disponibles para realizar la conexion.")


    #Esta clase realiza la coneccion a un instrumento. El parametro resource solamente
    #indica la posicion en la que se guardara el intrumento en el array de open resources.
    def connect(self, resource):
        self.resources = self.resourceManager.list_resources()  #Se pide al resource manager que muestre los intrumentos disponibles para la conexion
        print("Lista de resources disponibles: ", self.resources)
        print("Seleccionar el resource al que se quiere conectar con un numero empezando desde 0.")
        self.conected = False
        while (not self.conected):          #Este bloque while se repite hasta que la entrada del usuario sea valida.
            self.chosenResource = input()   #La entrada debe ser numerica y no ser mayor a la cantidad de instrumentos disponibles.
            if (self.chosenResource.isnumeric()):
                if (int(self.chosenResource) < len(self.resources)):
                    logging.info("Intentando abrir el resource: ")
                    logging.info(self.resources[(int(self.chosenResource))])
                    try:
                        res = self.resourceManager.open_resource(self.resources[int(self.chosenResource)], read_termination='\n', write_termination='\n') #Se conecta al instrumento
                        if(resource == OSC_RESOURC):                        #Se asigna el instrumento a la posicion elegida
                            self.resource = Resources.Oscilloscope(res)
                        elif(resource == GEN_RESOURC):
                            self.resource = Resources.Generator(res)
                        self.openResources.append(self.resource) #Se anade el instrumento a la lista
                        self.conected = True
                        return True
                    except visa.VisaIOError:
                        logging.critical("Error con el instrumento abierto.")
                        return False
                else:
                    print("Entrada mayor a la cantidad de resources disponibles. Intentar de nuevo.")
            else:
                print("La entrada debe ser numerica. Intentar de nuevo.")


    #Esta clase se encarga de pedirle al usuario la informacion sobre como se quiere realizar el bode.
    def bode_input_gathering(self):
        start_freq = 0
        stop_freq = 0
        point_per_decade_quantity = 0

        if (self.impedance_meas):
            print("Se esta actualmente midiendo una impedancia de entrada.\n"
                  "Se utilizara el primer canal que se seleccione como la tension\n"
                  "del generador y se utilizara el segundo canal seleccionado\n"
                  "como la tension despues de la resistencia que se anade\n"
                  "para medir impedancia. Presionar enter.")
            input()
            good_input = False
            print(
                "Ingresar valor de la resistencia sobre la que se mide la corriente.\n"
                "Se dividira la tension medida sobre esta resistencia por el valor ingresado.")
            while (not good_input):
                self.impedance_resistor = input()
                try:
                    self.impedance_resistor = float(self.impedance_resistor)
                    if (self.impedance_resistor >= 0.1 and self.impedance_resistor <= 10000000):
                        good_input = True
                    else:
                        print("Intente nuevamente con una entrada numerica entre 0.1 y 10000000.")
                except ValueError:
                    print("Intente nuevamente con una entrada numerica.")


        print("Ingresar nombre del archivo a guardar en la carpeta de Mediciones.")
        while(True):
            self.filename = input()
            if(self.filename != ""):
                break

        # Configuracion de canales
        good_input = False
        print(
            "Se desea utilizar escala [L]ineal o lo[G]aritmica para la frecuencia?")
        while (not good_input):
            self.freqscale = input()
            if (self.freqscale == 'L' or self.freqscale == 'l'):
                self.freqscale = 'l'
                good_input = True
            elif (self.freqscale == 'G' or self.freqscale == 'g'):
                self.freqscale = 'g'
                good_input = True
            else:
                print(
                    "Intente nuevamente. [L]ineal o lo[G]aritmico")

        #Se pide la frecuencia de arranque y se valida
        good_input = False
        if(self.freqscale == 'g'):
            print("Ingresar el exponente decimal de la frecuencia de arranque. Debe ser entre 1 y 7.\n"
                  "Si se quiere multiplicar la frecuencia elegida por un numero de una\n"
              "sola cifra, utilizar una coma luego del exponente. Ejemplo para 500KHz: 5,5")
        else:
            print("Ingresar la frecuencia de arraque:")
        while (not good_input):
            start_freq = input()
            if(start_freq.find(',') != -1):
                start_freq = start_freq.split(',')
                self.mult = start_freq[1]
                start_freq = start_freq[0]
                if (start_freq.isnumeric()):
                    start_freq = float(start_freq)
                    if (start_freq >= 1 and start_freq <= 7):
                        good_input = True
                    else:
                        print("Intente nuevamente con una entrada numerica entre 1 y 7.")
                else:
                    print("Intente nuevamente con una entrada numerica entre 1 y 7.")
                if (self.mult.isnumeric()):
                    self.mult = float(self.mult)
                    if (self.mult >= 1 and self.mult <= 9):
                        good_input = True
                    else:
                        print("Intente nuevamente con una entrada numerica entre 1 y 9.")
                else:
                    print("Intente nuevamente con una entrada numerica entre 1 y 9.")
            else:
                if (start_freq.isnumeric()):
                    start_freq = float(start_freq)
                    if(self.freqscale == 'g'):
                        if (start_freq >= 1 and start_freq <= 7):
                            good_input = True
                            self.mult = 1
                        else:
                            print("Intente nuevamente con una entrada numerica entre 1 y 7.")
                    else:
                        if(start_freq >=1 and start_freq <= 10*10**6):
                            good_input = True
                            self.mult = 1
                        else:
                            print("Intente nuevamente con una entrada numerica entre 1 y 10MHz.")
                else:
                    print("Intente nuevamente con una entrada numerica entre 1 y 7.")

        #Se pide la frecuencia final y se valida
        good_input = False

        if(self.freqscale == 'g'):
            print("Ingresar el exponente decimal de la frecuencia final. Debe ser entre 1 y 7.\n"
                  "Si se quiere multiplicar la frecuencia elegida por un numero de una\n"
              "sola cifra, utilizar una coma luego del exponente. Ejemplo para 500KHz: 5,5")
        else:
            print("Ingresar la frecuencia de arraque:")
        while (not good_input):
            stop_freq = input()
            if (stop_freq.find(',') != -1):
                stop_freq = stop_freq.split(',')
                self.multstop = stop_freq[1]
                stop_freq = stop_freq[0]
                if (stop_freq.isnumeric()):
                    stop_freq = float(stop_freq)
                    if (stop_freq >= 1 and stop_freq <= 7):
                        good_input = True
                    else:
                        print("Intente nuevamente con una entrada numerica entre 1 y 7.")
                else:
                    print("Intente nuevamente con una entrada numerica entre 1 y 7.")
                if (self.multstop.isnumeric()):
                    self.multstop = float(self.multstop)
                    if (self.multstop >= 1 and self.multstop <= 9):
                        good_input = True
                    else:
                        print("Intente nuevamente con una entrada numerica entre 1 y 9.")
                else:
                    print("Intente nuevamente con una entrada numerica entre 1 y 9.")
            else:
                if (stop_freq.isnumeric()):
                    stop_freq = float(stop_freq)
                    if (self.freqscale == 'g'):
                        if (stop_freq >= 1 and stop_freq <= 7):
                            good_input = True
                            self.multstop = 1
                        else:
                            print("Intente nuevamente con una entrada numerica entre 1 y 7.")
                    else:
                        if (stop_freq >= 1 and stop_freq <= 10 * 10 ** 6):
                            good_input = True
                            self.multstop = 1
                        else:
                            print("Intente nuevamente con una entrada numerica entre 1 y 10MHz.")
                else:
                    print("Intente nuevamente con una entrada numerica entre 1 y 7.")

        good_input = False
        print(
            "Se desea agregar mediciones sobre frecuencias particulares? [y/n]")
        while (not good_input):
            self.particularfreq = input()
            if (self.particularfreq == 'n' or self.particularfreq == 'N'):
                self.particularfreq = 0
                good_input = True
            elif (self.particularfreq == 'y' or self.particularfreq == 'Y'):
                self.particularfreq = 1
                good_input = True
            else:
                print(
                    "Intente nuevamente. [y/n]")
        self.particular_frequencies=[]
        if(self.particularfreq):

            good_input = False
            print("Ingresar frecuencias EN HERTZ y SEPARADAS POR COMA")
            while (not good_input):
                particularf = input()
                particularf = particularf.split(',')
                for ff in particularf:
                    try:
                        ff = float(ff)
                        if (ff >= 1 and ff<= 15*10**6):
                            good_input = True
                            self.particular_frequencies.append(int(ff))
                        else:
                            print("Intente nuevamente con una entrada numerica entre 1 y 15M.")
                            good_input = False
                    except ValueError:
                        print("Intente nuevamente con una entrada numerica.")

        #Se piden la cantidad de puntos por decada y se valida
        good_input = False
        if(self.freqscale == 'g'):
            print("Cantidad de puntos por decada:")
        else:
            print("Cantidad de puntos:")
        while (not good_input):
            point_per_decade_quantity = input()
            if (point_per_decade_quantity.isnumeric()):
                point_per_decade_quantity = float(point_per_decade_quantity)
                if (point_per_decade_quantity >= 1 and point_per_decade_quantity <= 1000):
                    good_input = True
                else:
                    print("Intente nuevamente con una entrada numerica entre 1 y 10000.")
            else:
                print("Intente nuevamente con una entrada numerica entre 1 y 10000.")

        #Se calcula la cantidad de puntos total y se realiza el array con todas las frecuencias a las que se va a medir
        if (start_freq == stop_freq):
            if(self.freqscale == 'g'):
                self.f = [10 ** start_freq]
            else:
                self.f = [start_freq]
        else:
            if(self.freqscale == 'g'):
                self.f = [500,1000,1500,2000,2500,3000,3500,4000,4500,5000,5500,6000,6500,7000,7500,8000,8500,9000,9500,10000]#np.logspace(np.log10(self.mult*(10**start_freq)), np.log10(self.multstop*(10**stop_freq)), point_per_decade_quantity * (stop_freq - start_freq))
            elif(self.freqscale == 'l'):
                self.f = [500,1000,1500,2000,2500,3000,3500,4000,4500,5000,5500,6000,6500,7000,7500,8000,8500,9000,9500,10000]

        for ff in self.f:
            ff = int(ff)

        for pf in self.particular_frequencies:
            inserted = False
            temp = 0
            if(pf < self.f[0]):
                self.f=np.insert(self.f, 0, pf)
            else:
                for ff in self.f:
                    if (ff <= pf):
                        pass
                    else:
                        self.f = np.insert(self.f, temp, pf)
                        inserted=True
                        break
                    temp = temp + 1
                if(not inserted):
                    self.f=np.insert(self.f,temp,pf)

        print("Frecuencias a medir:")
        print(self.f)

        #Se pide la tension del generador y se valida
        good_input = False
        print("Ingresar tension pico a pico para el generador de funciones:")
        while (not good_input):
            self.voltage = input()
            try:
                self.voltage = float(self.voltage)/2
                if (self.voltage >= 0.01 and self.voltage/2 <= 10):
                    good_input = True
                    self.voltage = self.voltage
                else:
                    print("Intente nuevamente con una entrada numerica entre 0.01 y 10.")
            except ValueError:
                print("Intente nuevamente con una entrada numerica.")


        #Se pide el primer canal a medir y se valida
        good_input = False
        print("Ingresar primer canal para medir. Ingresar 0 si se quiere seleccionar el canal MATH.")
        print("Se tomaran los canales de la siguiente forma para los settings de las mediciones:")
        print("Primer canal ---> Segundo canal")
        if(self.impedance_meas):
            print("Recordar que se debe elegir la tension del generador como el primer canal y la\ntension despues de la resistencia como segundo canal.")
        while (not good_input):
            self.chan1 = input()
            if (self.chan1.isnumeric()):
                self.chan1 = int(self.chan1)
                if (self.chan1 == 1 or self.chan1 == 2 or self.chan1 == 3 or self.chan1 == 4 or self.chan1 == 0):
                    good_input = True
                    self.chan.append(self.chan1)
                else:
                    print("Intente nuevamente con una entrada numerica entre 0 y 5.")
            else:
                print("Intente nuevamente con una entrada numerica entre 0 y 5.")

        #Se pide el segundo canal para medir y se valida
        good_input = False
        print("Ingresar segundo canal para medir. Ingresar 0 si se quiere seleccionar el canal MATH.")
        while (not good_input):
            self.chan2 = input()
            if (self.chan2.isnumeric()):
                self.chan2 = int(self.chan2)
                if (self.chan2 == 1 or self.chan2 == 2 or self.chan2 == 3 or self.chan2 == 4 or self.chan2 == 0 and self.chan2 != self.chan1):
                    good_input = True
                    self.chan.append(self.chan2)
                else:
                    print("Intente nuevamente con una entrada numerica entre 0 y 5 y que sea distinta del primer canal.")
            else:
                print("Intente nuevamente con una entrada numerica entre 0 y 5 y que sea distinta del primer canal.")

        self.usingmath = False
        if(self.chan[FIRST_CHANNEL] == 0 or self.chan[SECOND_CHANNEL] == 0):
            good_input = False
            self.usingmath = True
            print("Ingresar operacion que se desea utilizar para el canal MATH: [+,-,*]")
            while (not good_input):
                self.math_oper = input()
                if(self.math_oper == '+' or self.math_oper == '-' or self.math_oper == '*'):
                    good_input = True
                else:
                    print("Ingresar +, - o *.")
            good_input = False
            print("Ingresar que canales se quieren utilizar como source para math separados por coma. Ejemplo: 2,1")
            while(not good_input):
                self.math_sources=input()
                self.math_sources = self.math_sources.split(',')
                if(len(self.math_sources) == 2 and
                    int(self.math_sources[0]) > 0 and
                    int(self.math_sources[1]) > 0 and
                    int(self.math_sources[0]) <=4 and
                    int(self.math_sources[1]) <=4):
                    good_input = True
                    self.chan.append(int(self.math_sources[0]))
                    self.chan.append(int(self.math_sources[1]))
                else:
                    print("Se deben de ingresar los canales de forma numerica y separados por coma. Ejemplo: 3,1")

        #Tiempo minimo de establecimiento
        good_input = False
        print("Establecer un tiempo minimo de establecimiento para tomar las mediciones.")
        while (not good_input):
            self.minwaittime = input()
            try:
                self.minwaittime = float(self.minwaittime)
                if (self.minwaittime >= 0 and self.minwaittime <= 15):
                    good_input = True
                else:
                    print("Intente nuevamente con una entrada numerica entre 0 y 15 segundos")
            except ValueError:
                print("Intente nuevamente con una entrada numerica.")

        # Configuracion de canales
        good_input = False
        print("Se desea usar high resolution para bajas frecuencias y average (32 puntos) para altas frecuencias? [y/n]")
        while (not good_input):
            self.acqchoice = input()
            if (self.acqchoice == 'n' or self.acqchoice == 'N'):
                self.acqchoice = 0
                good_input = True
            elif(self.acqchoice == 'y' or self.acqchoice == 'Y'):
                self.acqchoice = 1
                good_input = True
            else:
                print(
                    "Intente nuevamente. [y/n]")
        if(self.acqchoice):
            # Se pide la tension del generador y se valida
            good_input = False
            print("Ingresar cantidad de pantallas a promediar para el averaging: 1, 2, 4, 8, 16, 32, 64, 128, 256..")
            while (not good_input):
                self.avgcount = input()
                try:
                    self.avgcount = float(self.avgcount)
                    if (self.avgcount >= 1 and self.avgcount <= 8192):
                        good_input = True
                    else:
                        print("Intente nuevamente con una entrada numerica entre 1 y 8192.")
                except ValueError:
                    print("Intente nuevamente con una entrada numerica.")

        # Configuracion de canales
        good_input = False
        print(
            "Se desea usar AC coupling? [y/n]")
        while (not good_input):
            self.accoupchoice = input()
            if (self.accoupchoice == 'n' or self.accoupchoice == 'N'):
                self.accoupchoice = 0
                good_input = True
            elif (self.accoupchoice == 'y' or self.accoupchoice == 'Y'):
                self.accoupchoice = 1
                good_input = True
            else:
                print(
                    "Intente nuevamente. [y/n]")

        # Configuracion de canales
        good_input = False
        print(
            "Se desea utilizar trigger externo? [y/n] (RECOMENDADO)")
        while (not good_input):
            self.trigext = input()
            if (self.trigext == 'n' or self.trigext == 'N'):
                self.trigext = 0
                good_input = True
            elif (self.trigext == 'y' or self.trigext == 'Y'):
                self.trigext = 1
                good_input = True
            else:
                print(
                    "Intente nuevamente. [y/n]")

        if(not self.trigext):
            # Configuracion de canales
            good_input = False
            print(
                "Se desea usar HF reject y noise reject en el trigger? [y/n]")
            while (not good_input):
                self.trigfilterchoice = input()
                if (self.trigfilterchoice == 'n' or self.trigfilterchoice == 'N'):
                    self.trigfilterchoice = 0
                    good_input = True
                elif (self.trigfilterchoice == 'y' or self.trigfilterchoice == 'Y'):
                    self.trigfilterchoice = 1
                    good_input = True
                else:
                    print(
                        "Intente nuevamente. [y/n]")

        # Configuracion de canales
        good_input = False
        print(
            "Se desea utilizar las puntas en x10? [y/n]")
        while (not good_input):
            self.probe10 = input()
            if (self.probe10 == 'n' or self.probe10 == 'N'):
                self.probe10 = 0
                good_input = True
            elif (self.probe10 == 'y' or self.probe10 == 'Y'):
                self.probe10 = 1
                good_input = True
            else:
                print(
                    "Intente nuevamente. [y/n]")


        print("RECORDATORIO: CONECTAR ALIMENTACION DEL CIRCUITO. \nPONER PUNTAS EN X10 Y CALIBRARLAS SI ES NECESARIO.\n"
              "PRESIONAR ENTER PARA COMENZAR LA MEDICION.")
        input()

    #Esta clase es el algoritmo que setea al generador y osciloscopio en las configuraciones necesarias para cada punto en el que se va a medir
    def bode(self):
        self.oscilloscope = self.openResources[OSC_RESOURC]
        self.generator = self.openResources[GEN_RESOURC]
        self.chan = []
        self.bode_input_gathering() #Se pide informacion sobre como se quiere realizar el bode
        self.phasef = self.f

        if(self.usingmath):
            self.oscilloscope.set_math_operation(self.math_oper)
            self.oscilloscope.set_math_source(self.chan[MATH_SOURCE_1], self.chan[MATH_SOURCE_2])
        #AC-COUPLING
        if(self.accoupchoice):
            for channel in self.chan:
                self.oscilloscope.chan_coup(Resources.SET, channel, Resources.COUP_AC)

        #EXTERNAL TRIGGER
        if(self.trigext):
            self.oscilloscope.trig_source(Resources.SET, Resources.TRIG_EXTERNAL)
        #HFREJECT hasta 100khz
        elif(self.trigfilterchoice):
            self.oscilloscope.trig_hfreject(Resources.SET, Resources.TRIG_HFREJ_ON)

        #CONFIGURACION DEL OSCILOSCOPIO
        if(self.impedance_meas):
            self.oscilloscope.set_impedance_meas(self.chan[FIRST_CHANNEL], self.chan[SECOND_CHANNEL])
        else:
            self.oscilloscope.set_bode_meas(self.chan[FIRST_CHANNEL], self.chan[SECOND_CHANNEL]) #Se configura al osciloscopio para realizar un bode, mediciones de ratio, phase, etc.

        #CONFIGURACION GENERADOR
        self.generator.set_voltage(self.voltage) #Se configura al generador con la tension elegida
        self.generator.set_output(1)

        #PROBETAS
        if(self.probe10):
            for channel in self.chan:
                if(channel != 0):
                    self.oscilloscope.chan_probe(Resources.SET, channel, 10)

        self.ratio=[]
        self.phase=[]
        self.imp=[]

        #Algoritmo que se corre para cada punto en el que se va a querer medir.
        first_fit = True
        self.chan_divs=[]
        for i in range(-3, 1, 1):
            for j in [1, 2, 5]:
                self.chan_divs.append(j*10**(i))

        self.chan_indexes = []
        for channel in self.chan:
            self.chan_indexes.append(0)

        for ff in (self.f):

            #Cortar hfreject del trigger si freq muy alta
            if(ff > HFREJECT_CUTOFF):
                self.oscilloscope.trig_hfreject(Resources.SET, Resources.TRIG_HFREJ_OFF)
            else:
                self.oscilloscope.trig_noisereject(Resources.SET, Resources.TRIG_NREJ_ON)

            #Para ver si quepa la senal sacar filtros
            self.oscilloscope.acq_type(Resources.SET, Resources.ACQUIRE_TYPE_NORMAL)

            self.generator.set_frequency(ff)                        #Se setea la frecuencia en el generador
            self.oscilloscope.tim_div(Resources.SET, 1/((2)*ff))           #Se setea la frecuencia del osciloscopio

            exit_while = False

            #Primer fitteo en la pantalla para ambas senales
            if(first_fit):
                temp=0
                for channel in self.chan:
                    for div in self.chan_divs:
                        self.oscilloscope.chan_div(Resources.SET, channel, div)
                        time.sleep(3 * (1 / (np.power(ff, (1 / 6)))))
                        if(not self.oscilloscope.is_clipping(channel)):
                            break
                        else:
                            self.chan_indexes[temp] =+ 1
                    temp =+ 1

                temp = 0
                if(self.usingmath):
                    for channel in self.chan:
                        if(channel == 0):
                            for div in self.chan_divs:
                                self.oscilloscope.chan_div(Resources.SET, channel, div)
                                time.sleep(3 * (1 / (np.power(ff, (1 / 6)))))
                                if (not self.oscilloscope.is_clipping(channel)):
                                    break
                                else:
                                    self.chan_indexes[temp] = + 1
                        temp =+ 1

                first_fit = False

            #Se fija si con la nueva frecuencia la senal sigue entrando

            temp = 0
            for channel in self.chan:
                while (not self.oscilloscope.is_big_enough(channel)):
                    if (self.chan_indexes[temp] > 0):
                        self.chan_indexes[temp] = self.chan_indexes[temp] - 1
                        self.oscilloscope.chan_div(Resources.SET, channel, self.chan_divs[self.chan_indexes[temp]])
                        time.sleep(3 * (1 / (np.power(ff, (1 / 6)))))
                    else:
                        break
                while (self.oscilloscope.is_clipping(channel)):
                    if (self.chan_indexes[temp] < len(self.chan_divs) - 2):
                        self.chan_indexes[temp] = self.chan_indexes[temp] + 1
                    else:
                        break
                    self.oscilloscope.chan_div(Resources.SET, channel, self.chan_divs[self.chan_indexes[temp]])
                    time.sleep(3 * (1 / (np.power(ff, (1 / 6)))))
                temp =+ 1

            temp = 0
            for channel in self.chan:
                if(channel == 0):
                    while (not self.oscilloscope.is_big_enough(channel)):
                        if (self.chan_indexes[temp] > 0):
                            self.chan_indexes[temp] = self.chan_indexes[temp] - 1
                            self.oscilloscope.chan_div(Resources.SET, channel, self.chan_divs[self.chan_indexes[temp]])
                            time.sleep(3 * (1 / (np.power(ff, (1 / 6)))))
                        else:
                            break
                    while (self.oscilloscope.is_clipping(channel)):
                        if (self.chan_indexes[temp] < len(self.chan_divs) - 2):
                            self.chan_indexes[temp] = self.chan_indexes[temp] + 1
                        else:
                            break
                        self.oscilloscope.chan_div(Resources.SET, channel, self.chan_divs[self.chan_indexes[temp]])
                        time.sleep(3 * (1 / (np.power(ff, (1 / 6)))))
                temp = + 1

            #Luego de hacer entrar la senal, pone los filtros para medir
            if(self.acqchoice):
                if(ff <= HIGH_RES_CUTOFF):
                    self.oscilloscope.acq_type(Resources.SET, Resources.ACQUIRE_TYPE_HIGH_RES)
                else:
                    self.oscilloscope.acq_type(Resources.SET, Resources.ACQUIRE_TYPE_AVERAGE)
                    self.oscilloscope.acq_average_count(Resources.SET, self.avgcount)

            med=self.oscilloscope.measure_stats(ff, self.minwaittime)  #Se le pide al osciloscopio las mediciones
            med = med.split(',')
            if(not self.impedance_meas):
                self.ratio.append(float(med[0]))
                self.phase.append(float(med[1]))
            else:

                vpp1 = float(med[0])
                vpp2 = float(med[1])
                pha = np.radians(float(med[2]))

                v1=cmath.rect(vpp1, 0)
                v2=cmath.rect(vpp2, pha)

                self.impedance=( ( v2 * self.impedance_resistor ) / ( v1 - v2 ) )

                self.imp.append(abs(self.impedance))
                self.phase.append(np.rad2deg(cmath.phase(self.impedance)))

            if (self.impedance_meas):
                #print("Frequency: " + str(float(med[2])))
                print("Impedance: " + str(abs(self.impedance)))
                print("Phase: " + str(np.rad2deg(cmath.phase(self.impedance))))
            else:
                #print("Frequency: " + str(float(med[2])))
                print("Ratio: " + str(float(med[0])))
                print("Phase: " + str(float(med[1])))

        for i in range(0, len(self.phase), 1):
            if(self.phase[i] == float(Resources.OOR_VAL)):
                print("WARNING: Error in phase measurement. Setting particular measurement to 0.")
                self.phase[i] = 0

        good_meas=False
        while(not good_meas):

            plt.title("VISTA PREVIA DE LA MEDICION, FALTA CONFIRMAR")
            plt.xscale("log")
            plt.grid(True)
            plt.xlabel("Frecuencia [Hz]")
            if(not self.impedance_meas):
                plt.ylabel("Amplitud [db]")
                plt.plot(self.f, self.ratio, label="Amplitud")
            else:
                plt.ylabel("Impedancia [Ohm]")
                plt.plot(self.f, self.imp, label="Impedancia")
            plt.legend()
            plt.show()
            plt.title("VISTA PREVIA DE LA MEDICION, FALTA CONFIRMAR")
            plt.grid(True)
            plt.xscale("log")
            plt.xlabel("Frecuencia [Hz]")
            plt.ylabel("Fase [Grados]")
            plt.plot(self.f, self.phase, label="Fase")
            plt.legend()
            plt.show()

            good_input = False
            print(
                "Se desean eliminar las mediciones a partir de una cierta frecuencia? [y/n]")
            while (not good_input):
                self.elim = input()
                if (self.elim == 'n' or self.elim == 'N'):
                    self.elim = False
                    good_meas = True
                    good_input = True
                elif (self.elim == 'y' or self.elim == 'Y'):
                    self.elim = True
                    good_input = True
                else:
                    print(
                        "Intente nuevamente. [y/n]")

            if(self.elim):
                good_input = False
                print("Ingresar frecuencia hasta la cual se quieren guardar las mediciones.")
                while (not good_input):
                    self.limitfreq = input()
                    if (self.limitfreq.isnumeric()):
                        self.limitfreq = int(self.limitfreq)
                        if (self.limitfreq >= 10 and self.limitfreq <= 9000000):
                            good_input = True
                        else:
                            print("Intente nuevamente con una entrada numerica entre 10 y 9000000.")
                    else:
                        print("Intente nuevamente con una entrada numerica entre 10 y 9000000.")

                freq_temp = 0
                exitwhile = False
                for ff in self.f:
                    if(ff >  self.limitfreq):
                        self.f=np.delete(self.f,self.f.index(ff))
                        self.phase=np.delete(self.phase,self.f.index(ff))
                        if(self.impedance_meas):
                            self.imp=np.delete(self.imp,self.f.index(ff))
                        else:
                            self.ratio=np.delete(self.imp,self.f.index(ff))

        scriptfile = os.path.dirname(__file__)

        if(not self.impedance_meas):

            if (not os.path.exists(scriptfile + "/../Mediciones/CSV/Bode/" + self.filename + ".csv")):
                self.filepath = scriptfile + "/../Mediciones/CSV/Bode/" + self.filename + ".csv"
            else:
                for i in range(1, 10, 1):
                    if (not os.path.exists(scriptfile + "/../Mediciones/CSV/Bode/" + self.filename + "(" + str(i) + ")" + ".csv")):
                        self.filepath = scriptfile + "/../Mediciones/CSV/Bode/" + self.filename + "(" + str(i) + ")" + ".csv"
                        break
        else:
            if (not os.path.exists(scriptfile + "/../Mediciones/CSV/Impedance/" + self.filename + ".csv")):
                self.filepath = scriptfile + "/../Mediciones/CSV/Impedance/" + self.filename + ".csv"
            else:
                for i in range(1, 10, 1):
                    if (not os.path.exists(scriptfile + "/../Mediciones/CSV/Impedance/" + self.filename + "(" + str(i) + ")" + ".csv")):
                        self.filepath = scriptfile + "/../Mediciones/CSV/Impedance/" + self.filename + "(" + str(i) + ")" + ".csv"
                        break

        with open(self.filepath, 'w+') as csvfile:
            writer = csv.writer(csvfile)
            if(not self.impedance_meas):
                writer.writerow(["frequency", "MAG", "PHA"])
                for i in range(0, len(self.f), 1):
                    writer.writerow([str(self.f[i]), str(self.ratio[i]), str(self.phase[i])])
            else:
                writer.writerow(["frequency", "Z", "PHA"])
                for i in range(0, len(self.f), 1):
                    writer.writerow([str(self.f[i]), str(self.imp[i]), str(self.phase[i])])
        csvfile.close()

    def ask_which_measurement(self):
        print("Elegir que se quiere hacer: [E]xit, [B]ode o Impedancia de entrada[Z].")
        self.impedance_meas = False
        bad_input = True
        while(bad_input):
            inp = input()
            if(inp == 'E' or inp == 'e'):
                return EXIT
            elif(inp == 'B' or inp == 'b'):
                return BODE
            elif(inp == 'Z' or inp == 'z'):
                return IMPEDANCE
            elif(inp=='guidin'):
                return EASTER
            else:
                print("Ingresar nuevamente una entrada alfabetica igual a E, Z o B.")