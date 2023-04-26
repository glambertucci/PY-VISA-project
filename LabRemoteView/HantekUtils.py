class HantekOscilloscopeWG:
    def __init__(self, resource_manager):
        self.hantek = resource_manager
        if self.hantek.query(':DDS:SWITch?') == 'OFF':
            self.hantek.write(':DDS:SWITch 1')
        self.aquire_modes = ['NORMAL','AVERAGE','PEAK','HRESOLUTION']
    def set_vertical_scale(self, channel: int, scale: float):
        self.hantek.write(':CHANnel' + str(channel) + ':SCALe ' + "{:.3e}".format(scale))

    def set_horizontal_scale(self, scale: float):
        self.hantek.write('TIMebase:SCALe ' + "{:.3e}".format(scale))
    def set_aquire_mode(self,mode:str):
        if mode.upper() in self.aquire_modes:
            self.hantek.write(':ACQuire:TYPE '+mode)
            if(mode.upper() == 'AVERAGE'):
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
