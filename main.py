# Install pyvisa, pyvisa-py, pyusb

import sys
import numpy as np
import math
from scipy import interpolate
from scipy import signal
from datetime import datetime
from pathlib import Path

import oscilloscope
import generator
import plot as Plotter


# Currently used scope is Hantek DSO4204B, needs to be broadly set manually to show signals first
# Currently used signal generator is Uni-t UTG932E/UTG962E

# Remember to set scope trigger to NORMAL mode

def decade_space(start, end, points_per_decade):
    ndecades = math.log10(end) - math.log10(start)
    npoints = int(ndecades) * points_per_decade
    return np.logspace(math.log10(start), math.log10(end), num=npoints, endpoint=True, base=10)


def _filter(in_signal, sampling_f, signal_f):
    nyquist_f = sampling_f / 2
    filter_pb = (4*signal_f) / nyquist_f
    sos = signal.ellip(6, 0.02, 50, [filter_pb], output='sos')
    return signal.sosfiltfilt(sos, in_signal)


def main():
    osc = oscilloscope.Oscilloscope("CN1725001000247")
    awg = generator.Generator("AWG1222270183")

    # Set sweep frequency range here
    freq_min = 1000  # 10Hz
    freq_max = 800e3  # 100kHz
    points_per_decade = 10
    averaging = 2
    averaging_limit_f = 10e3
    filtering = True

    # Here you can set points of AWG voltage to frequency chart
    # Keep in mind that you NEED to set last point to higher frequency than used during sweep
    # The same for low frequency (the best - start from zero here)
    # [frequency point, milli volts]
    # voltages = np.array([[0, 1000], [1000, 5000], [10e3, 10000], [100e3, 15000], [100e6, 1000]])
    voltages = np.array([[0, 700], [2000, 700], [20000, 300], [100e6, 300]])
    # voltages = np.array([[0, 500], [1000, 500], [3000, 300], [5000, 100], [100e6, 100]])

    frequencies = []
    amplification = []
    phase = []

    voltage = interpolate.interp1d(voltages[:, 0], voltages[:, 1], kind='linear')

    for freq in decade_space(freq_min, freq_max, points_per_decade):
        osc.set_timebase(freq)
        awg.set_frequency(freq)
        awg.set_amplitude(voltage(freq) / 1000)

        if freq > averaging_limit_f:
            averaging = 1

        print('*** STARTING DOWNLOAD ***')
        scaled_data, sampling_freq = osc.acquire()
        for i in range(averaging - 1):
            scaled_data1, sampling_freq1 = osc.acquire()
            scaled_data[0] = np.add(scaled_data[0], scaled_data1[0])
            scaled_data[1] = np.add(scaled_data[1], scaled_data1[1])
        scaled_data[0] = np.divide(scaled_data[0], averaging)
        scaled_data[1] = np.divide(scaled_data[1], averaging)

        if filtering:
            scaled_data[0] = _filter(scaled_data[0], sampling_freq, freq)
            scaled_data[1] = _filter(scaled_data[1], sampling_freq, freq)
        print('*** DOWNLOAD COMPLETE ***')

        ch1_vpp = abs(scaled_data[0].min()) + abs(scaled_data[0].max())
        ch2_vpp = abs(scaled_data[1].min()) + abs(scaled_data[1].max())
        amp = 20 * math.log10(ch2_vpp / ch1_vpp)

        correlation = signal.correlate(scaled_data[0], scaled_data[1], mode='full')
        lags = signal.correlation_lags(scaled_data[0].size, scaled_data[1].size, mode='full')
        samples_per_period = sampling_freq / freq
        # TODO: filter out lags where difference > +/- 180 deg
        lag = (lags[np.argmax(correlation)] / samples_per_period) * 360

        if lag > 180:
            while lag > 180:
                lag -= 360
        elif lag < -180:
            while lag < -180:
                lag += 360

        frequencies.append(freq)
        amplification.append(amp)
        phase.append(lag)
        print('f = ' + str(freq) + 'Hz, amp = ' + str(amp) + 'dB, lag = ' + str(lag) + 'deg')

    awg.set_off()

    del awg
    del osc

    Path("./data").mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    data = np.array([frequencies, amplification, phase])
    np.save('./data/' + timestamp + '_data.npy', data)

    plt = Plotter.plot(data)
    plt.show()
    plt.savefig('./data/' + timestamp + '_plot.png')


if __name__ == '__main__':
    sys.exit(main())

