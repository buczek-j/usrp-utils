#!/usr/bin/python3
from tranceiver_ofdm_usrp import tranceiver_ofdm_usrp
import signal

def main():
    '''
    '''
    tb = tranceiver_ofdm_usrp(input_port_num="55555", output_port_num="55556", rx_bw=0.5e6, rx_freq=2e9, rx_gain=0.8, serial_num="31C9237", tx_bw=0.5e6, tx_freq=1e9, tx_gain=0.8)

    def sig_handler(sig=None, frame=None):
        tb.stop()
        tb.wait()

        sys.exit(0)

    signal.signal(signal.SIGINT, sig_handler)
    signal.signal(signal.SIGTERM, sig_handler)

    tb.start()

    try:
        input('Press Enter to quit: ')
    except EOFError:
        pass
    tb.stop()
    tb.wait()


if __name__ == '__main__':
    main()