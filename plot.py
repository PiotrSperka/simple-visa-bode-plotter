import matplotlib.ticker as ticker
import matplotlib.pyplot as plt
import numpy as np


def plot(data):
    frequencies = data[0]
    amplification = data[1]
    phase = data[2]

    fig, ax1 = plt.subplots()
    fig.suptitle('Magnitude and phase vs frequency')
    ax1.set_xscale("log")
    ax1.xaxis.set_major_locator(ticker.LogLocator(base=10))
    ax1.xaxis.set_minor_formatter(ticker.NullFormatter())
    ax1.set_ylabel("Magnitude [dB]", color='blue')
    ax1.set_xlabel("Frequency [Hz]")
    ax1.grid(color='green', linestyle='--', linewidth=0.5)
    ax1.set_xlim(frequencies.min(), frequencies.max())

    ax2 = ax1.twinx()  # instantiate a second axes that shares the same x-axis
    ax2.set_ylabel("Phase [deg]", color='red')
    ax2.grid(color='green', linestyle='--', linewidth=0.5)

    ax1.plot(frequencies, amplification, linestyle='--', marker='o', color='blue')
    ax2.plot(frequencies, phase, linestyle='--', marker='o', color='red')
    ax2.set_yticks(np.linspace(ax2.get_yticks()[0], ax2.get_yticks()[-1], len(ax1.get_yticks())))
    ax1.set_yticks(np.linspace(ax1.get_yticks()[0], ax1.get_yticks()[-1], len(ax1.get_yticks())))

    fig.tight_layout()  # otherwise the right y-label is slightly clipped
    fig.autofmt_xdate()

    return fig


if __name__ == '__main__':
    input_data = np.load('test_data.npy')
    plt = plot(input_data)
    plt.show()
    # plt.savefig('test.png')

