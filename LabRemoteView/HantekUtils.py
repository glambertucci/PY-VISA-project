import time


class HantekOscilloscopeWG:
    def __init__(self, resource_manager):
        self.hantek = resource_manager
        self.acquire_modes = ['NORMAL', 'AVERAGE', 'PEAK', 'HRESOLUTION']
        self.trigger_modes = ['EDGE', 'PULSE', 'TV', 'SLOPE', 'TIMEOUT', 'WINDOW', 'PATTERN', 'INTERVAL', 'UNDERTHROW',
                              'UART', 'LIN', 'CAN', 'SPI', 'IIC']
        if self.hantek.query(':DDS:SWITch?') == 'OFF':
            self.hantek.write(':DDS:SWITch 1')
        self.set_trigger_mode('EDGE')
        self.hantek.write('MEASure:ENABle ON')
        self.horizontal_scale = [8.e-01, 3.2e-01, 1.6e-01, 8.e-02, 3.2e-02, 1.6e-02,
                                 8.e-03, 3.2e-03, 1.6e-03, 8.e-04, 3.2e-04, 1.6e-04,
                                 8.e-05, 3.2e-05, 1.6e-05, 8e-06, 3.2e-06, 1.6e-06,
                                 8.e-07, 3.2e-07, 1.6e-07]
        self.vertical_scale = [10 * 8, 5 * 8, 2 * 8, 1 * 8, 10e-1 * 8, 5e-1 * 8, 2e-1 * 8, 1e-1 * 8, 5e-2 * 8, 2e-2 * 8,
                               1e-2 * 8, 5e-3 * 8, 2e-3 * 8]

    # Setters
    def set_vertical_scale(self, channel: int, scale: float):
        self.hantek.write(':CHANnel' + str(channel) + ':SCALe ' + "{:.3e}".format(scale / 8))

    def set_horizontal_scale(self, scale: float):
        self.hantek.write('TIMebase:Range ' + "{:.3e}".format(scale))

    def set_acquire_mode(self, mode: str):
        if mode.upper() in self.acquire_modes:
            self.hantek.write(':ACQuire:TYPE ' + mode)
            if mode.upper() == 'AVERAGE':
                self.hantek.write(':ACQuire:COUNt 128')

    def set_probe(self, channel: int = 1, x1: bool = True, x10: bool = False):
        invalid = x1 ^ x10
        if not invalid:
            if x1:
                self.hantek.write(':CHANnel' + str(channel) + ':PROBe 1')
            else:
                self.hantek.write(':CHANnel' + str(channel) + ':PROBe 10')
            return 1
        else:
            return -1

    def set_waveform(self, signal_type: str, vpp: int, frequency: int, duty: int = 50):
        if self.waveform_specs_valid(signal_type, vpp, frequency, duty):
            self.hantek.write(':DDS:TYPE ' + signal_type)
            self.hantek.write(':DDS:FREQ ' + str(frequency))
            self.hantek.write(':DDS:AMP ' + str(vpp))
            self.hantek.write(':DDS:DUTY ' + str(duty))

    def set_trigger_mode(self, mode):
        if mode.upper() in self.trigger_modes:
            self.hantek.write('TRIGger:MODE ' + str(mode))

    def set_meas_channel(self, channel):
        self.hantek.write('MEASure:SOURce CHANnel' + str(channel))

    def measure_VPP(self, channel):
        self.hantek.write('MEASure:CHANnel' + str(channel) + ':ITEM VPP')
        return self.hantek.query('MEASure:CHANnel' + str(channel) + ':ITEM? VPP')

    def measure_VP(self, channel):
        self.hantek.write('MEASure:CHANnel' + str(channel) + ':ITEM VMAX')
        return self.hantek.query('MEASure:CHANnel' + str(channel) + ':ITEM? VMAX')

    #  Getters
    def get_trigger_state(self):
        return self.hantek.query('TRIGger:STATus?')

    def get_vertical_scale(self, channel: int):
        return self.hantek.query(':CHANnel' + str(channel) + ':SCALe?')

    # Modify
    def modify_waveform_frequency(self, frequency: int):
        self.hantek.write(':DDS:FREQ ' + str(frequency))

    def modify_waveform_duty(self, duty: int):
        self.hantek.write(':DDS:DUTY ' + str(duty))

    @staticmethod
    def waveform_specs_valid(signal_type, vpp, frequency, duty):
        res = False
        if signal_type == 'SINE' and (vpp > 0 or vpp < 7 or frequency > 0 or frequency < 25e6):
            res |= True
        elif signal_type == 'SQUARE' and (
                vpp > 0 or vpp < 7 or frequency > 0 or frequency < 10e6 or duty > 0 or duty < 99):
            res |= True
        elif signal_type == 'RAMP' and (vpp > 0 or vpp < 7 or frequency > 0 or frequency < 1e6):
            res |= True
        elif signal_type == 'EXP' and (vpp > 0 or vpp < 7 or frequency > 0 or frequency < 5e6):
            res |= True
        elif signal_type in ['NOISE', 'DC', 'ARB1', 'ARB2', 'ARB3', 'ARB4']:
            res |= True
        return res
