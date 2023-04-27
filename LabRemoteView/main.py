# This is a sample Python script.
import pyvisa
from HantekUtils import HantekOscilloscopeWG
import time
# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.




# Press the green button in the gutter to run the script.

resourceManager = pyvisa.ResourceManager()
list_of_resources = resourceManager.list_resources()
print(list_of_resources)
if(len(list_of_resources) > 0 ):
    res = resourceManager.open_resource(list_of_resources[0])
    osc = HantekOscilloscopeWG(res)
    osc.set_waveform('SINE', 5, 1000)
    # for f in range(1000,2000,10):
    #     osc.modify_waveform_frequency(f)
    # osc.set_waveform('SQUARE',5,1000)
    # for f in range(1,99,1):
    #     osc.modify_waveform_duty(f)
    # osc.set_vertical_scale(1,2.5)
#    osc.set_horizontal_scale(150e-6)
#    osc.set_acquire_mode('hresolution')
#    print(osc.get_trigger_state())
#    osc.set_trigger_mode("EDGE")
    print(osc.measure_VPP(1))
# See PyCharm help at https://www.jetbrains.com/help/pycharm/
