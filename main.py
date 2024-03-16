# Install pyvisa, pyvisa-py, pyusb

import sys
import numpy as np
import scipy.signal as signal
import math
from scipy import interpolate
from datetime import datetime

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


def main():
    osc = oscilloscope.Oscilloscope("CN1725001000247")
    awg = generator.Generator("AWG1222270183")

    # Set sweep frequency range here
    freq_min = 10  # 10Hz
    freq_max = 1000e3  # 100kHz
    points_per_decade = 10

    # Here you can set points of AWG voltage to frequency chart
    # Keep in mind that you NEED to set last point to higher frequency than used during sweep
    # The same for low frequency (the best - start from zero here)
    # [frequency point, milli volts]
    voltages = np.array([[0, 1000], [1000, 5000], [10e3, 10000], [100e3, 15000], [100e6, 1000]])

    frequencies = []
    amplification = []
    phase = []

    voltage = interpolate.interp1d(voltages[:, 0], voltages[:, 1], kind='linear')

    for freq in decade_space(freq_min, freq_max, points_per_decade):
        osc.set_timebase(freq)
        awg.set_frequency(freq)
        awg.set_amplitude(voltage(freq) / 1000)

        print('*** STARTING DOWNLOAD ***')
        scaled_data, sampling_freq = osc.acquire()
        print('*** DOWNLOAD COMPLETE ***')

        ch1_vpp = abs(scaled_data[0].min()) + abs(scaled_data[0].max())
        ch2_vpp = abs(scaled_data[1].min()) + abs(scaled_data[1].max())
        amp = 20 * math.log10(ch2_vpp / ch1_vpp)

        correlation = signal.correlate(scaled_data[0], scaled_data[1], mode='full')
        lags = signal.correlation_lags(scaled_data[0].size, scaled_data[1].size, mode='full')
        samples_per_period = sampling_freq / freq
        lag = (lags[np.argmax(correlation)] / samples_per_period) * 360

        frequencies.append(freq)
        amplification.append(amp)
        phase.append(lag)
        print('f = ' + str(freq) + 'Hz, amp = ' + str(amp) + 'dB, lag = ' + str(lag) + 'deg')

    awg.set_off()

    del awg
    del osc

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    data = np.array([frequencies, amplification, phase])
    np.save(timestamp + '_data.npy', data)

    plt = Plotter.plot(data)
    plt.show()
    plt.savefig(timestamp + '_plot.png')


if __name__ == '__main__':
    sys.exit(main())

