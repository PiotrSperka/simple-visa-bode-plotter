# Simple bode plotter
Simple bode plotter made out of oscilloscope and waveform generator driven by pyvisa

## Hardware
Application here is only a frontend for hardware which does the real job. Application is written to be used with:
* Hantek DSO4004B oscilloscope (DSO4204B in my case)
* UNI-T UTG900E waveform generator (UTG932E in my case)

Both devices are connected via USB to computer (USB SCPI) and are visible for pyVisa library.
So in terms of lab equipment it really can be anything which uses said protocol (ex USB, GPIB, Ethernet, ...).
Of course, small changes will be needed (check your device's programming manual for appropriate commands).

## Software
_WORK IN PROGRESS_

This simple software uses Python alongside with a few libraries, such as:

* numpy
* scipy
* matplotlib
* pyVisa

Application was written and tested on Mac, but should work absolutely fine also on Linux and Windows.

## More information
For more information go to https://sperka.pl