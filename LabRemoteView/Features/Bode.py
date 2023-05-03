# This bode diagram is not a bode per se, because it lacks the phase
import numpy as np


def bode_diagram(oscilloscope, fi: float, fo: float, vi: float, channel,number_of_points=20):
    frequencies = np.logspace(np.log10(fi), np.log10(fo), num=number_of_points)
    oscilloscope.set_waveform('SINE', vi, int(fi))
    measurements = []
    freqs = []
    for freq in frequencies:
        oscilloscope.modify_waveform_frequency(freq)
        adjust_horizontal_size(freq, oscilloscope, )
        measurement = adjust_vertical_size_and_measure(oscilloscope, channel)
        db_measurement = 20*np.log10(measurement / vi)
        measurements.append(db_measurement)
        freqs.append(int(freq))
    return measurements, freqs


def adjust_horizontal_size(freq, osc):
    best_size = 2 / freq
    actual_size = find_nearest(osc.horizontal_scale, best_size)
    osc.set_horizontal_scale(actual_size)


def adjust_vertical_size_and_measure(osc, channel):
    vp = float(osc.measure_VPP(channel))
    vs = float(osc.get_vertical_scale(channel)) * 8
    clipping = True
    could_zoom_in = True
    meas = -1
    if vp < vs * 0.98:
        clipping = False
    if vp > vs * 0.6:
        could_zoom_in = False
    if clipping:
        meas = zoom_out(osc, vs, channel)
    elif could_zoom_in:
        meas = zoom_in(osc, vs, channel)
    else:
        meas = float(osc.measure_VPP(channel))
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
            vp = float(osc.measure_VPP(channel))
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
    if array[idx] < value:
        return array[idx-1]
    else:
        return array[idx]
