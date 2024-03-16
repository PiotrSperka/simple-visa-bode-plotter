import pyvisa


class Generator:
    DEFAULT_TIMEOUT = 2000
    awg = None
    rm = None

    def __init__(self, serial):
        self.rm = pyvisa.ResourceManager()
        resources = self.rm.list_resources()
        print(resources)
        filtered = [k for k in resources if serial in k]

        if len(filtered) == 0:
            raise Exception("Cannot find oscilloscope")

        print('Opening ' + filtered[0])
        self.awg = self.rm.open_resource(filtered[0])
        self.awg.timeout = self.DEFAULT_TIMEOUT

        self._preset()

    def __del__(self):
        self.awg.close()
        self.rm.close()

    def _preset(self):
        self.awg.write('CHANnel1:OUTPut 0')
        self.awg.write('CHANnel1:LOAD 10000')
        self.awg.write('CHANnel1:AMPLitude:UNIT VPP')
        self.awg.write('CHANnel1:BASE:WAVe SINe')
        self.awg.write('CHANnel1:BASE:PHASe 0')
        self.awg.write('CHANnel1:BASE:AMPLitude 1')
        self.awg.write('CHANnel1:BASE:OFFSet 0')
        self.awg.write('CHANnel1:OUTPut 1')
        pass

    def set_frequency(self, frequency: float):
        self.awg.write('CHANnel1:BASE:FREQuency ' + str(frequency))

    def set_amplitude(self, amplitude: float):
        self.awg.write('CHANnel1:BASE:AMPLitude ' + str(amplitude))

    def set_off(self):
        self.awg.write('CHANnel1:OUTPut 0')

    def set_on(self):
        self.awg.write('CHANnel1:OUTPut 1')
