import array
import math
from time import sleep
import numpy as np
import pyvisa


class Object(object):
    pass


class Oscilloscope:
    VOLTAGE_FACTOR = 4.9e-318
    DEFAULT_TIMEOUT = 2000
    dso = None
    rm = None

    def __init__(self, serial):
        self.rm = pyvisa.ResourceManager()
        resources = self.rm.list_resources()
        print(resources)
        filtered = [k for k in resources if serial in k]

        if len(filtered) == 0:
            raise Exception("Cannot find oscilloscope")

        print('Opening ' + filtered[0])
        self.dso = self.rm.open_resource(filtered[0])
        self.dso.timeout = self.DEFAULT_TIMEOUT

        self._preset()

    def __del__(self):
        self.dso.close()
        self.rm.close()

    def _wait(self):
        self.dso.write('*OPC')
        ESRvalue = self.dso.query('*ESR?')
        while ESRvalue == int(ESRvalue) != 1:
            ESRvalue = self.dso.query('*ESR?')

    def _preset(self):
        self.dso.write('*CLS')
        self.dso.write('CHANnel1:COUPling AC')
        print(self.dso.query('CHANnel1:COUPling?'))
        self.dso.write('CHANnel2:COUPling AC')
        print(self.dso.query('CHANnel2:COUPling?'))
        self.dso.write('RUN ON')
        self._wait()

    def set_timebase(self, frequency):
        timebases = [2e-9, 5e-9, 10e-9, 20e-9, 50e-9, 100e-9, 200e-9, 500e-9,
                     1e-6, 2e-6, 5e-6, 10e-6, 20e-6, 50e-6, 100e-6, 200e-6, 500e-6,
                     1e-3, 2e-3, 5e-3, 10e-3, 20e-3, 50e-3, 100e-3, 200e-3, 500e-3,
                     1, 2, 5, 10, 20, 50, 100, 200, 500]

        timebase = 1 / frequency / 5  # 1/5th of a period
        closest_index = min(range(len(timebases)), key=lambda j: abs(timebases[j] - timebase))

        self.dso.write('TIMebase:SCALe ' + str(timebases[closest_index]))
        self._wait()

    def _acquire_data(self):
        # Wait for data acquisition
        wait = float(self.dso.query('TIMebase:RANGe?'))
        if wait < 1:
            wait = 1

        sleep(math.ceil(wait))

    def _read_binary(self, command: str, timeout=500):
        data = []
        self.dso.write(command)
        self.dso.timeout = timeout
        try:
            data = self.dso.read_bytes(1)
        except:
            self.dso.timeout = self.DEFAULT_TIMEOUT

        return data

    def _process_preamble(self, data: str):
        retobj = Object()
        if len(data) > 128:
            retobj.msg = 1
            retobj.w = None
            print('ERROR processing preamble')
            return retobj
        elif 128 >= len(data) >= 117:
            retobj.msg = 2
            print('Preamble has been read')
        else:
            retobj.msg = 3
            print('Another error occurred')
            return retobj

        # OBS: The Programming manual is wrong.
        # -For the CHs Voltages, it corresponds to 8 bits data
        # -Setting a CH Range of 1Volt returns 4.9e-318 in the querying.
        # -CH Scale correspond to Voltage_Range/10.

        retobj.w = Object()
        retobj.w.tmc_head = data[0:2]  # data[0]-data[1] (2 bits): Data header #9
        retobj.w.cur_len = data[2:11]  # data[2]-data[10] (9 bits): Indicates the byte length of the current data packet
        retobj.w.tot_len = data[
                           11:20]  # data[11]-data[19] (9 bits): The total length of bytes indicating the amount of data
        retobj.w.send_len = data[20:29]  # data[20]-data[28] (9 bits): Indicates the byte length of the uploaded data
        retobj.w.run_state = data[
                             29:30]  # data[29] (1 digit): Indicates the current running status 0 is paused 1 is running
        retobj.w.trig_state = data[
                              30:31]  # data[30] (1 digit): Indicates the state of the trigger 0 is no valid trigger 1 is valid trigger
        retobj.w.ch1_offset = data[31:35]  # data[31]-data[34] (4 bits): Indicates the offset of channel 1
        retobj.w.ch2_offset = data[35:39]  # data[35]-data[38] (4 bits): Indicates the offset of channel 2
        retobj.w.ch3_offset = data[39:43]  # data[39]-data[42] (4 bits): Indicates the offset of channel 3
        retobj.w.ch4_offset = data[43:47]  # data[43]-data[46] (4 bits): Indicates the offset of channel 4
        retobj.w.CH1_voltage = data[
                               47:55]  # data[47]-data[54] (8 bits): Indicates the voltage of channel 1  1 V Range == 4.9e-318
        retobj.w.CH2_voltage = data[
                               55:63]  # data[55]-data[62] (8 bits): Indicates the voltage of channel 2  1 V Range == 4.9e-318
        retobj.w.CH3_voltage = data[
                               63:71]  # data[63]-data[70] (8 bits): Indicates the voltage of channel 3  1 V Range == 4.9e-318
        retobj.w.CH4_voltage = data[
                               71:79]  # data[71]-data[78] (8 bits): Indicates the voltage of channel 4  1 V Range == 4.9e-318
        retobj.w.ch_enabled = data[79:83]  # data[79]-data[82] (4 bits): Indicates the status of the channel.
        # See instructions for details
        retobj.w.sampling_rate = data[83:92]  # data[83]-data[91] (9 bits): Indicates the sampling rate
        retobj.w.extract_len = data[92:98]  # data[92]-data[97] (6 bits): indicates the sampling multiple
        retobj.w.trig_time = data[98:107]  # data[98]-data[106] (9 bits): Display trigger time of current frame
        retobj.w.start_time = data[
                              107:116]  # data[107]-data[115] (9 bits): The start time point of the acquisition start point of the current frame display data
        retobj.w.Reserve_data = data[116:len(data)]  # data[116]-data[127] (12 bits?): reserved
        # The data read later is valid waveform data
        # Preparing waveform data reading...
        retobj.w.send_len_data = int(retobj.w.send_len)  # String converted to number
        retobj.w.cur_len_data = int(retobj.w.cur_len)  # String converted to number
        retobj.w.tot_len_data = int(retobj.w.tot_len)  # String converted to number

        return retobj

    def _scale_data(self, preamble, data, probe_factors):  #float(preamble.w.CH1_voltage)
        return_data = []
        voltages = [float(preamble.w.CH1_voltage), float(preamble.w.CH2_voltage), float(preamble.w.CH3_voltage), float(preamble.w.CH4_voltage)]
        for i in range(0, 4):
            rang = voltages[i] * probe_factors[i] / self.VOLTAGE_FACTOR
            ch_range = rang * 10
            adc2volt = ch_range / (2 ** 8 - 1)  # 8 bit adc
            return_data.append(data[i] * adc2volt)

        return return_data

    def _split_channels(self, preamble, data):
        channels = preamble.w.ch_enabled[0] - 48 + preamble.w.ch_enabled[1] - 48 + preamble.w.ch_enabled[2] - 48 + preamble.w.ch_enabled[3] - 48
        samples_per_channel = len(data) / channels
        retval = []
        for i in range(4):
            if preamble.w.ch_enabled[i] == 49:  # 49 is "1" ascii
                retval.append(data[int(i * samples_per_channel):int((i + 1)*samples_per_channel)])
            else:
                retval.append(np.array([]))

        return retval

    def _get_curve(self):
        ranges = [5, 10, 20, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 50000, 100000]
        probe_factors = [10, 10, 1, 1]
        # PREAMBLE
        preamble = self._read_binary('WAVEFORM:DATA:ALL?')
        processed_preamble = self._process_preamble(preamble)
        if processed_preamble.msg != 2:
            print("Preamble failed, retry")
            return self._get_curve()

        overall_data = []
        overall_length = 0
        while overall_length < processed_preamble.w.tot_len_data:
            binary = self._read_binary('WAVEFORM:DATA:ALL?', 300)
            overall_data += binary[29:-1]
            overall_length = int(binary[20:29]) + int(binary[2:11]) - 29

        # byte date is signed byte in reality
        data_array = array.array('b')
        data_array.frombytes(bytes(overall_data))
        # scale data to show value in volts
        split_channels = self._split_channels(processed_preamble, np.array(data_array))
        scaled_channels = self._scale_data(processed_preamble, split_channels, probe_factors)

        channel_voltages = np.array([float(processed_preamble.w.CH1_voltage)/self.VOLTAGE_FACTOR*1000, float(processed_preamble.w.CH2_voltage)/self.VOLTAGE_FACTOR*1000, float(processed_preamble.w.CH3_voltage)/self.VOLTAGE_FACTOR*1000, float(processed_preamble.w.CH4_voltage)/self.VOLTAGE_FACTOR*1000]) * np.array(probe_factors)
        changed_settings = False

        # TODO: set sensitivity based on filtered value?
        for i in range(0, 4):
            if len(split_channels[i]) > 0:
                if split_channels[i].min() < -125 or split_channels[i].max() > 125:
                    current_index = min(range(len(ranges)), key=lambda j: abs(ranges[j]-channel_voltages[i]))
                    if current_index < len(ranges) - 1:
                        print('Channel ' + str(i) + ' is out of range')
                        self.set_sensitivity(i, ranges[current_index + 1] * probe_factors[i])
                        changed_settings = True
                elif split_channels[i].min() > -49 and split_channels[i].max() < 49:
                    current_index = min(range(len(ranges)), key=lambda j: abs(ranges[j] - channel_voltages[i]))
                    if current_index > 0:
                        print('Channel ' + str(i) + ' should be more sensitive')
                        self.set_sensitivity(i, ranges[current_index - 1] * probe_factors[i])
                        changed_settings = True

        if changed_settings:
            self._acquire_data()
            return self._get_curve()

        return scaled_channels, float(processed_preamble.w.sampling_rate)

    def set_sensitivity(self, channel, sensitivity):
        print('Setting sensitivity [' + str(channel) + '] to ' + str(sensitivity))
        self.dso.write('CHANnel' + str(channel + 1) + ':RANGe ' + str(sensitivity) + ' mV')
        self._wait()

    def acquire(self):
        self._acquire_data()
        return self._get_curve()
