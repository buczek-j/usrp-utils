import uhd, signal, sys
from numpy import empty, complex64


CLOCK_TIMEOUT = 1000  # 1000mS timeout for external clock locking
INIT_DELAY = 0.05  # 50mS initial delay before transmit

class USRP_RX():
    def __init__(self, freq, bandwidth, gain=30.0, rate=1e6, lo_offset=0.0, antenna='RX2', channel=0, serial_num=None, type_string='b200', verbose=False):
        '''
        Method to handle a usrp receiver
        :param freq: float for the center frequency in Hz
        :param bandwidth: float for the analog filter bandwidth in Hz
        :param gain: float for the rx gain in dB
        :param rate: float for the rx sampling rate in bps
        :param lo_offset: float for the optional LO offset
        :param antenna: string for the USRP RX antenna
        :param channel: int for the channel number
        :param serial_num: string optional for the serial number of the USRP (uses type otherwise)
        :param type_string: string for the usrp type 
        :param verbose: bool for if verbose printing should be used
        '''
        self.verbose = verbose
        self.channel = channel

        # connect to the usrp
        if serial_num == None:
            self.usrp = uhd.usrp.MultiUSRP("type="+type_string)
        else:
            self.usrp = uhd.usrp.MultiUSRP("serial="+serial_num)

        # Set the antenna and channel
        self.usrp.set_rx_subdev_spec(uhd.usrp.SubdevSpec('A:A'))  
        if channel >= self.usrp.get_rx_num_channels():
            raise RuntimeError("Invalid channel selected")
        self.usrp.set_rx_antenna(antenna, channel)

        # Set the rate
        self.usrp.set_rx_rate(rate, channel)
        if abs(self.usrp.get_rx_rate(channel) - rate) > 1.0:
            print("~ Actual rate: {} Msps".format(self.usrp.get_rx_rate(channel) / 1e6))

        # Set the frequency
        tr = uhd.types.TuneRequest(freq, lo_offset)
        self.usrp.set_rx_freq(tr, channel)

        # Set gain reference level
        self.usrp.set_rx_gain(gain, channel)
        
        # Set bandwidth
        self.usrp.set_rx_bandwidth(bandwidth, channel)
        if abs(self.usrp.get_rx_bandwidth(channel) - bandwidth) > 1.0:
            print("ALMOST. Actual bandwidth: {} MHz".format(self.usrp.get_rx_bandwidth(channel) / 1e6))

        self.stream = self.get_streamer()

    def get_temp(self):
        '''
        Method to get the current internal temperature of the usrp
        :return: string temperature in celcius
        '''
        return self.usrp.get_rx_sensor('temp').value
    
    def get_rssi(self):
        '''
        Method to get the current rssi value of the usrp
        :return: string rssi in dB
        '''
        return self.usrp.get_rx_sensor('rssi').value
    
    def get_rx_rate(self):
        '''
        Method to get the rx rate in bps
        '''
        return self.usrp.get_rx_rate()

    def get_streamer(self, rx_cpu='fc32', rx_otw='sc16'):
        '''
        return an RX streamer
        :param rx_cpu: string to specify the host/cpu sample mode for RX
        :param rx_otw: string to specify the over-the-wire sample mode for RX
        :return: rx_streamer
        '''
        stream_args = uhd.usrp.StreamArgs('fc32', 'sc16')
        stream_args.channels = [self.channel]
        return self.usrp.get_rx_stream(stream_args)
    
    def get_buffer(self):
        '''
        '''
        # Make a receive buffer
        num_channels = self.stream.get_num_channels()
        max_samps_per_packet = self.stream.get_max_num_samps()
        self.recv_buffer = empty((num_channels, max_samps_per_packet), dtype=complex64)
        metadata = uhd.types.RXMetadata()

        # Craft and send the Stream Command
        stream_cmd = uhd.types.StreamCMD(uhd.types.StreamMode.start_cont)
        stream_cmd.stream_now = (num_channels == 1)
        stream_cmd.time_spec = uhd.types.TimeSpec(self.usrp.get_time_now().get_real_secs() + INIT_DELAY)
        self.stream.issue_stream_cmd(stream_cmd)

        num_rx_samps = 0
        while True:
            try:
                samps= self.stream.recv(self.recv_buffer, metadata) * num_channels
                if samps >0:
                    num_rx_samps += samps
                    print(self.recv_buffer[0:samps])
            except RuntimeError as ex:
                print("Runtime error in receive: %s", ex)
                return

        # # To estimate the number of dropped samples in an overflow situation, we need the following
        # # On the first overflow, set had_an_overflow and record the time
        # # On the next ERROR_CODE_NONE, calculate how long its been since the recorded time, and use the
        # #   tick rate to estimate the number of dropped samples. Also, reset the tracking variables
        # had_an_overflow = False
        # last_overflow = uhd.types.TimeSpec(0)
        # # Setup the statistic counters
        # num_rx_samps = 0
        # num_rx_dropped = 0
        # num_rx_overruns = 0
        # num_rx_seqerr = 0
        # num_rx_timeouts = 0
        # num_rx_late = 0

        # rate = self.usrp.get_rx_rate()
        # # Receive until we get the signal to stop
        # while not timer_elapsed_event.is_set():
        #     try:
        #         num_rx_samps += rx_streamer.recv(recv_buffer, metadata) * num_channels
        #     except RuntimeError as ex:
        #         print("Runtime error in receive: %s", ex)
        #         return

        #     # Handle the error codes
        #     if metadata.error_code == uhd.types.RXMetadataErrorCode.none:
        #         # Reset the overflow flag
        #         if had_an_overflow:
        #             had_an_overflow = False
        #             num_rx_dropped += uhd.types.TimeSpec(
        #                 metadata.time_spec.get_real_secs() - last_overflow.get_real_secs()
        #             ).to_ticks(rate)
        #     elif metadata.error_code == uhd.types.RXMetadataErrorCode.overflow:
        #         had_an_overflow = True
        #         last_overflow = metadata.time_spec
        #         # If we had a sequence error, record it
        #         if metadata.out_of_sequence:
        #             num_rx_seqerr += 1
        #             print("Detected RX sequence error.")
        #         # Otherwise just count the overrun
        #         else:
        #             num_rx_overruns += 1
        #     elif metadata.error_code == uhd.types.RXMetadataErrorCode.late:
        #         print("Receiver error: %s, restarting streaming...", metadata.strerror())
        #         num_rx_late += 1
        #         # Radio core will be in the idle state. Issue stream command to restart streaming.
        #         stream_cmd.time_spec = uhd.types.TimeSpec(
        #             self.usrp.get_time_now().get_real_secs() + INIT_DELAY)
        #         stream_cmd.stream_now = (num_channels == 1)
        #         self.stream.issue_stream_cmd(stream_cmd)
        #     elif metadata.error_code == uhd.types.RXMetadataErrorCode.timeout:
        #         print("Receiver error: %s, continuing...", metadata.strerror())
        #         num_rx_timeouts += 1
        #     else:
        #         print("Receiver error: %s", metadata.strerror())
        #         print("Unexpected error on receive, continuing...")

        # # Return the statistics to the main thread
        # rx_statistics["num_rx_samps"] = num_rx_samps
        # rx_statistics["num_rx_dropped"] = num_rx_dropped
        # rx_statistics["num_rx_overruns"] = num_rx_overruns
        # rx_statistics["num_rx_seqerr"] = num_rx_seqerr
        # rx_statistics["num_rx_timeouts"] = num_rx_timeouts
        # rx_statistics["num_rx_late"] = num_rx_late
        # # After we get the signal to stop, issue a stop command
        self.stream.issue_stream_cmd(uhd.types.StreamCMD(uhd.types.StreamMode.stop_cont))

class USRP_TX():
    def __init__(self, freq, antenna='TX/RX'):
        '''
        '''

def main():
    usrp = USRP_RX(2.4e9, 5e6)
    usrp.get_buffer()
    return True

if __name__ == '__main__':
    main()