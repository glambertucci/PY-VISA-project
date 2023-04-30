# This bode diagram is not a bode per se, because it lacks the phase
import numpy as np


def bode_diagram(oscilloscope, fi: float, fo: float, vi: float, channel):
    frequencies = np.logspace(np.log10(fi), np.log10(fo), num=20)
    oscilloscope.set_waveform('SINE', vi, int(fi))
    measurements = []
    for freq in frequencies:
        print('Doing frequency: ', freq)
        oscilloscope.modify_waveform_frequency(freq)
        adjust_horizontal_size(freq, oscilloscope, )
        measurements.append([freq, adjust_vertical_size_and_measure(oscilloscope, channel)])
    return measurements


def adjust_horizontal_size(freq, osc):
    best_size = 2 / freq
    actual_size = find_nearest(osc.horizontal_scale, best_size)
    osc.set_horizontal_scale(actual_size)
    print('Did horizontal adjustment')


def adjust_vertical_size_and_measure(osc, channel):
    vp = float(osc.measure_VP(channel))
    vs = float(osc.get_vertical_scale(channel)) * 8
    print(vs)
    clipping = True
    could_zoom_in = True
    meas = -1
    if vp < vs * 0.98:
        clipping = False
        print('Its not clipping')
    if vp > vs * 0.5:
        could_zoom_in = False
        print('It doesnt need to be zoomed in')
    if clipping:
        print('Zooming out')
        meas = zoom_out(osc, vs, channel)
    elif could_zoom_in:
        print('Zooming in')
        meas = zoom_in(osc, vs, channel)
    return meas


def zoom_in(osc, vs, channel):
    not_done = True
    actual_vs = vs
    vp = -1
    i = osc.vertical_scale.index(actual_vs)
    while not_done:
        if i == len(osc.vertical_scale) - 1:
            not_done = False
        else:
            i = i + 1
            actual_vs = osc.vertical_scale[i]
            osc.set_vertical_scale(channel, actual_vs)
            vp = float(osc.measure_VP(channel))
            if vp * 2 > actual_vs * 0.4:
                not_done = False
    return vp


def zoom_out(osc, vs, channel):
    not_done = True
    actual_vs = vs
    vp = -1
    while not_done:
        i = osc.vertical_scale.index(actual_vs)
        if i == 0:
            not_done = False
        else:
            i = i - 1
            actual_vs = osc.vertical_scale[i]
            osc.set_vertical_scale(channel, actual_vs)
            vp = float(osc.measure_VP(channel))
            if vp * 2 < actual_vs * 0.9:
                not_done = False
    return vp


def find_nearest(array, value):
    array = np.asarray(array)
    idx = (np.abs(array - value)).argmin()
    return array[idx]
