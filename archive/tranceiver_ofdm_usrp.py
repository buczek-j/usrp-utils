#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#
# SPDX-License-Identifier: GPL-3.0
#
# GNU Radio Python Flow Graph
# Title: tranceiver_ofdm_usrp
# Author: bucz
# GNU Radio version: v3.8.2.0-67-ge7bb5eda

from distutils.version import StrictVersion

if __name__ == '__main__':
    import ctypes
    import sys
    if sys.platform.startswith('linux'):
        try:
            x11 = ctypes.cdll.LoadLibrary('libX11.so')
            x11.XInitThreads()
        except:
            print("Warning: failed to XInitThreads()")

from gnuradio import blocks
import numpy
from gnuradio import digital
from gnuradio import fft
from gnuradio.fft import window
from gnuradio import gr
from gnuradio.filter import firdes
import sys
import signal
from PyQt5 import Qt
from argparse import ArgumentParser
from gnuradio.eng_arg import eng_float, intx
from gnuradio import eng_notation
from gnuradio import uhd
import time
from gnuradio.digital.utils import tagged_streams

from gnuradio import qtgui

class tranceiver_ofdm_usrp(gr.top_block, Qt.QWidget):

    def __init__(self, input_port_num="55555", output_port_num="55556", rx_bw=0.5e6, rx_freq=2e9, rx_gain=0.8, serial_num="31C9237", tx_bw=0.5e6, tx_freq=2.0e9, tx_gain=1):
        gr.top_block.__init__(self, "tranceiver_ofdm_usrp")
        Qt.QWidget.__init__(self)
        self.setWindowTitle("tranceiver_ofdm_usrp")
        qtgui.util.check_set_qss()
        try:
            self.setWindowIcon(Qt.QIcon.fromTheme('gnuradio-grc'))
        except:
            pass
        self.top_scroll_layout = Qt.QVBoxLayout()
        self.setLayout(self.top_scroll_layout)
        self.top_scroll = Qt.QScrollArea()
        self.top_scroll.setFrameStyle(Qt.QFrame.NoFrame)
        self.top_scroll_layout.addWidget(self.top_scroll)
        self.top_scroll.setWidgetResizable(True)
        self.top_widget = Qt.QWidget()
        self.top_scroll.setWidget(self.top_widget)
        self.top_layout = Qt.QVBoxLayout(self.top_widget)
        self.top_grid_layout = Qt.QGridLayout()
        self.top_layout.addLayout(self.top_grid_layout)

        self.settings = Qt.QSettings("GNU Radio", "tranceiver_ofdm_usrp")

        try:
            if StrictVersion(Qt.qVersion()) < StrictVersion("5.0.0"):
                self.restoreGeometry(self.settings.value("geometry").toByteArray())
            else:
                self.restoreGeometry(self.settings.value("geometry"))
        except:
            pass

        ##################################################
        # Parameters
        ##################################################
        self.input_port_num = input_port_num
        self.output_port_num = output_port_num
        self.rx_bw = rx_bw
        self.rx_freq = rx_freq
        self.rx_gain = rx_gain
        self.serial_num = serial_num
        self.tx_bw = tx_bw
        self.tx_freq = tx_freq
        self.tx_gain = tx_gain

        ##################################################
        # Variables
        ##################################################
        self.pilot_symbols = pilot_symbols = ((1, 1, 1, -1,),)
        self.pilot_carriers = pilot_carriers = ((-21, -7, 7, 21,),)
        self.payload_mod = payload_mod = digital.constellation_qpsk()
        self.packet_length_tag_key = packet_length_tag_key = "packet_len"
        self.occupied_carriers = occupied_carriers = (list(range(-26, -21)) + list(range(-20, -7)) + list(range(-6, 0)) + list(range(1, 7)) + list(range(8, 21)) + list(range(22, 27)),)
        self.length_tag_key = length_tag_key = "frame_len"
        self.header_mod = header_mod = digital.constellation_bpsk()
        self.fft_len = fft_len = 64
        self.sync_word2 = sync_word2 = [0j, 0j, 0j, 0j, 0j, 0j, (-1+0j), (-1+0j), (-1+0j), (-1+0j), (1+0j), (1+0j), (-1+0j), (-1+0j), (-1+0j), (1+0j), (-1+0j), (1+0j), (1+0j), (1 +0j), (1+0j), (1+0j), (-1+0j), (-1+0j), (-1+0j), (-1+0j), (-1+0j), (1+0j), (-1+0j), (-1+0j), (1+0j), (-1+0j), 0j, (1+0j), (-1+0j), (1+0j), (1+0j), (1+0j), (-1+0j), (1+0j), (1+0j), (1+0j), (-1+0j), (1+0j), (1+0j), (1+0j), (1+0j), (-1+0j), (1+0j), (-1+0j), (-1+0j), (-1+0j), (1+0j), (-1+0j), (1+0j), (-1+0j), (-1+0j), (-1+0j), (-1+0j), 0j, 0j, 0j, 0j, 0j]
        self.sync_word1 = sync_word1 = [0., 0., 0., 0., 0., 0., 0., 1.41421356, 0., -1.41421356, 0., 1.41421356, 0., -1.41421356, 0., -1.41421356, 0., -1.41421356, 0., 1.41421356, 0., -1.41421356, 0., 1.41421356, 0., -1.41421356, 0., -1.41421356, 0., -1.41421356, 0., -1.41421356, 0., 1.41421356, 0., -1.41421356, 0., 1.41421356, 0., 1.41421356, 0., 1.41421356, 0., -1.41421356, 0., 1.41421356, 0., 1.41421356, 0., 1.41421356, 0., -1.41421356, 0., 1.41421356, 0., 1.41421356, 0., 1.41421356, 0., 0., 0., 0., 0., 0.]
        self.samp_rate = samp_rate = 10000
        self.rolloff = rolloff = 0
        self.payload_equalizer = payload_equalizer = digital.ofdm_equalizer_simpledfe(fft_len, payload_mod.base(), occupied_carriers, pilot_carriers, pilot_symbols, 1)
        self.packet_len = packet_len = 256
        self.header_formatter = header_formatter = digital.packet_header_ofdm(occupied_carriers, n_syms=1, len_tag_key=packet_length_tag_key, frame_len_tag_key=length_tag_key, bits_per_header_sym=header_mod.bits_per_symbol(), bits_per_payload_sym=payload_mod.bits_per_symbol(), scramble_header=False)
        self.header_equalizer = header_equalizer = digital.ofdm_equalizer_simpledfe(fft_len, header_mod.base(), occupied_carriers, pilot_carriers, pilot_symbols)
        self.hdr_format = hdr_format = digital.header_format_ofdm(occupied_carriers, 1, length_tag_key,)

        ##################################################
        # Blocks
        ##################################################
        self.uhd_usrp_sink_0 = uhd.usrp_sink(
            ",".join(("", "")),
            uhd.stream_args(
                cpu_format="fc32",
                args='',
                channels=list(range(0,1)),
            ),
            packet_length_tag_key,
        )
        self.uhd_usrp_sink_0.set_samp_rate(tx_bw)
        self.uhd_usrp_sink_0.set_time_now(uhd.time_spec(time.time()), uhd.ALL_MBOARDS)

        self.uhd_usrp_sink_0.set_center_freq(tx_freq, 0)
        self.uhd_usrp_sink_0.set_antenna('TX/RX', 0)
        self.uhd_usrp_sink_0.set_normalized_gain(tx_gain, 0)
        self.fft_vxx_0_0 = fft.fft_vcc(fft_len, False, (), True, 1)
        self.digital_protocol_formatter_bb_0 = digital.protocol_formatter_bb(hdr_format, packet_length_tag_key)
        self.digital_ofdm_cyclic_prefixer_0 = digital.ofdm_cyclic_prefixer(
            fft_len,
            fft_len + fft_len//4,
            rolloff,
            packet_length_tag_key)
        self.digital_ofdm_carrier_allocator_cvc_0 = digital.ofdm_carrier_allocator_cvc( fft_len, occupied_carriers, pilot_carriers, pilot_symbols, (sync_word1, sync_word2), packet_length_tag_key, True)
        self.digital_crc32_bb_0_0 = digital.crc32_bb(False, packet_length_tag_key, True)
        self.digital_chunks_to_symbols_xx_0_0 = digital.chunks_to_symbols_bc(payload_mod.points(), 1)
        self.digital_chunks_to_symbols_xx_0 = digital.chunks_to_symbols_bc(header_mod.points(), 1)
        self.blocks_tagged_stream_mux_0 = blocks.tagged_stream_mux(gr.sizeof_gr_complex*1, packet_length_tag_key, 0)
        self.blocks_stream_to_tagged_stream_0 = blocks.stream_to_tagged_stream(gr.sizeof_char, 1, packet_len, packet_length_tag_key)
        self.blocks_repack_bits_bb_0_1 = blocks.repack_bits_bb(8, payload_mod.bits_per_symbol(), packet_length_tag_key, False, gr.GR_LSB_FIRST)
        self.blocks_repack_bits_bb_0_0 = blocks.repack_bits_bb(8, 1, packet_length_tag_key, False, gr.GR_LSB_FIRST)
        self.blocks_multiply_const_vxx_0 = blocks.multiply_const_cc(0.05)
        self.analog_random_source_x_0 = blocks.vector_source_b(list(map(int, numpy.random.randint(0, 255, 1000))), True)


        ##################################################
        # Connections
        ##################################################
        self.connect((self.analog_random_source_x_0, 0), (self.blocks_stream_to_tagged_stream_0, 0))
        self.connect((self.blocks_multiply_const_vxx_0, 0), (self.uhd_usrp_sink_0, 0))
        self.connect((self.blocks_repack_bits_bb_0_0, 0), (self.digital_chunks_to_symbols_xx_0, 0))
        self.connect((self.blocks_repack_bits_bb_0_1, 0), (self.digital_chunks_to_symbols_xx_0_0, 0))
        self.connect((self.blocks_stream_to_tagged_stream_0, 0), (self.digital_crc32_bb_0_0, 0))
        self.connect((self.blocks_tagged_stream_mux_0, 0), (self.digital_ofdm_carrier_allocator_cvc_0, 0))
        self.connect((self.digital_chunks_to_symbols_xx_0, 0), (self.blocks_tagged_stream_mux_0, 0))
        self.connect((self.digital_chunks_to_symbols_xx_0_0, 0), (self.blocks_tagged_stream_mux_0, 1))
        self.connect((self.digital_crc32_bb_0_0, 0), (self.blocks_repack_bits_bb_0_1, 0))
        self.connect((self.digital_crc32_bb_0_0, 0), (self.digital_protocol_formatter_bb_0, 0))
        self.connect((self.digital_ofdm_carrier_allocator_cvc_0, 0), (self.fft_vxx_0_0, 0))
        self.connect((self.digital_ofdm_cyclic_prefixer_0, 0), (self.blocks_multiply_const_vxx_0, 0))
        self.connect((self.digital_protocol_formatter_bb_0, 0), (self.blocks_repack_bits_bb_0_0, 0))
        self.connect((self.fft_vxx_0_0, 0), (self.digital_ofdm_cyclic_prefixer_0, 0))


    def closeEvent(self, event):
        self.settings = Qt.QSettings("GNU Radio", "tranceiver_ofdm_usrp")
        self.settings.setValue("geometry", self.saveGeometry())
        event.accept()

    def get_input_port_num(self):
        return self.input_port_num

    def set_input_port_num(self, input_port_num):
        self.input_port_num = input_port_num

    def get_output_port_num(self):
        return self.output_port_num

    def set_output_port_num(self, output_port_num):
        self.output_port_num = output_port_num

    def get_rx_bw(self):
        return self.rx_bw

    def set_rx_bw(self, rx_bw):
        self.rx_bw = rx_bw

    def get_rx_freq(self):
        return self.rx_freq

    def set_rx_freq(self, rx_freq):
        self.rx_freq = rx_freq

    def get_rx_gain(self):
        return self.rx_gain

    def set_rx_gain(self, rx_gain):
        self.rx_gain = rx_gain

    def get_serial_num(self):
        return self.serial_num

    def set_serial_num(self, serial_num):
        self.serial_num = serial_num

    def get_tx_bw(self):
        return self.tx_bw

    def set_tx_bw(self, tx_bw):
        self.tx_bw = tx_bw
        self.uhd_usrp_sink_0.set_samp_rate(self.tx_bw)

    def get_tx_freq(self):
        return self.tx_freq

    def set_tx_freq(self, tx_freq):
        self.tx_freq = tx_freq
        self.uhd_usrp_sink_0.set_center_freq(self.tx_freq, 0)

    def get_tx_gain(self):
        return self.tx_gain

    def set_tx_gain(self, tx_gain):
        self.tx_gain = tx_gain
        self.uhd_usrp_sink_0.set_normalized_gain(self.tx_gain, 0)

    def get_pilot_symbols(self):
        return self.pilot_symbols

    def set_pilot_symbols(self, pilot_symbols):
        self.pilot_symbols = pilot_symbols
        self.set_header_equalizer(digital.ofdm_equalizer_simpledfe(self.fft_len, header_mod.base(), self.occupied_carriers, self.pilot_carriers, self.pilot_symbols))
        self.set_payload_equalizer(digital.ofdm_equalizer_simpledfe(self.fft_len, payload_mod.base(), self.occupied_carriers, self.pilot_carriers, self.pilot_symbols, 1))

    def get_pilot_carriers(self):
        return self.pilot_carriers

    def set_pilot_carriers(self, pilot_carriers):
        self.pilot_carriers = pilot_carriers
        self.set_header_equalizer(digital.ofdm_equalizer_simpledfe(self.fft_len, header_mod.base(), self.occupied_carriers, self.pilot_carriers, self.pilot_symbols))
        self.set_payload_equalizer(digital.ofdm_equalizer_simpledfe(self.fft_len, payload_mod.base(), self.occupied_carriers, self.pilot_carriers, self.pilot_symbols, 1))

    def get_payload_mod(self):
        return self.payload_mod

    def set_payload_mod(self, payload_mod):
        self.payload_mod = payload_mod

    def get_packet_length_tag_key(self):
        return self.packet_length_tag_key

    def set_packet_length_tag_key(self, packet_length_tag_key):
        self.packet_length_tag_key = packet_length_tag_key
        self.set_header_formatter(digital.packet_header_ofdm(self.occupied_carriers, n_syms=1, len_tag_key=self.packet_length_tag_key, frame_len_tag_key=self.length_tag_key, bits_per_header_sym=header_mod.bits_per_symbol(), bits_per_payload_sym=payload_mod.bits_per_symbol(), scramble_header=False))

    def get_occupied_carriers(self):
        return self.occupied_carriers

    def set_occupied_carriers(self, occupied_carriers):
        self.occupied_carriers = occupied_carriers
        self.set_hdr_format(digital.header_format_ofdm(self.occupied_carriers, 1, self.length_tag_key,))
        self.set_header_equalizer(digital.ofdm_equalizer_simpledfe(self.fft_len, header_mod.base(), self.occupied_carriers, self.pilot_carriers, self.pilot_symbols))
        self.set_header_formatter(digital.packet_header_ofdm(self.occupied_carriers, n_syms=1, len_tag_key=self.packet_length_tag_key, frame_len_tag_key=self.length_tag_key, bits_per_header_sym=header_mod.bits_per_symbol(), bits_per_payload_sym=payload_mod.bits_per_symbol(), scramble_header=False))
        self.set_payload_equalizer(digital.ofdm_equalizer_simpledfe(self.fft_len, payload_mod.base(), self.occupied_carriers, self.pilot_carriers, self.pilot_symbols, 1))

    def get_length_tag_key(self):
        return self.length_tag_key

    def set_length_tag_key(self, length_tag_key):
        self.length_tag_key = length_tag_key
        self.set_hdr_format(digital.header_format_ofdm(self.occupied_carriers, 1, self.length_tag_key,))
        self.set_header_formatter(digital.packet_header_ofdm(self.occupied_carriers, n_syms=1, len_tag_key=self.packet_length_tag_key, frame_len_tag_key=self.length_tag_key, bits_per_header_sym=header_mod.bits_per_symbol(), bits_per_payload_sym=payload_mod.bits_per_symbol(), scramble_header=False))

    def get_header_mod(self):
        return self.header_mod

    def set_header_mod(self, header_mod):
        self.header_mod = header_mod

    def get_fft_len(self):
        return self.fft_len

    def set_fft_len(self, fft_len):
        self.fft_len = fft_len
        self.set_header_equalizer(digital.ofdm_equalizer_simpledfe(self.fft_len, header_mod.base(), self.occupied_carriers, self.pilot_carriers, self.pilot_symbols))
        self.set_payload_equalizer(digital.ofdm_equalizer_simpledfe(self.fft_len, payload_mod.base(), self.occupied_carriers, self.pilot_carriers, self.pilot_symbols, 1))

    def get_sync_word2(self):
        return self.sync_word2

    def set_sync_word2(self, sync_word2):
        self.sync_word2 = sync_word2

    def get_sync_word1(self):
        return self.sync_word1

    def set_sync_word1(self, sync_word1):
        self.sync_word1 = sync_word1

    def get_samp_rate(self):
        return self.samp_rate

    def set_samp_rate(self, samp_rate):
        self.samp_rate = samp_rate

    def get_rolloff(self):
        return self.rolloff

    def set_rolloff(self, rolloff):
        self.rolloff = rolloff

    def get_payload_equalizer(self):
        return self.payload_equalizer

    def set_payload_equalizer(self, payload_equalizer):
        self.payload_equalizer = payload_equalizer

    def get_packet_len(self):
        return self.packet_len

    def set_packet_len(self, packet_len):
        self.packet_len = packet_len
        self.blocks_stream_to_tagged_stream_0.set_packet_len(self.packet_len)
        self.blocks_stream_to_tagged_stream_0.set_packet_len_pmt(self.packet_len)

    def get_header_formatter(self):
        return self.header_formatter

    def set_header_formatter(self, header_formatter):
        self.header_formatter = header_formatter

    def get_header_equalizer(self):
        return self.header_equalizer

    def set_header_equalizer(self, header_equalizer):
        self.header_equalizer = header_equalizer

    def get_hdr_format(self):
        return self.hdr_format

    def set_hdr_format(self, hdr_format):
        self.hdr_format = hdr_format




def argument_parser():
    parser = ArgumentParser()
    return parser


def main(top_block_cls=tranceiver_ofdm_usrp, options=None):
    if options is None:
        options = argument_parser().parse_args()

    if StrictVersion("4.5.0") <= StrictVersion(Qt.qVersion()) < StrictVersion("5.0.0"):
        style = gr.prefs().get_string('qtgui', 'style', 'raster')
        Qt.QApplication.setGraphicsSystem(style)
    qapp = Qt.QApplication(sys.argv)

    tb = top_block_cls()

    tb.start()

    tb.show()

    def sig_handler(sig=None, frame=None):
        Qt.QApplication.quit()

    signal.signal(signal.SIGINT, sig_handler)
    signal.signal(signal.SIGTERM, sig_handler)

    timer = Qt.QTimer()
    timer.start(500)
    timer.timeout.connect(lambda: None)

    def quitting():
        tb.stop()
        tb.wait()

    qapp.aboutToQuit.connect(quitting)
    qapp.exec_()

if __name__ == '__main__':
    main()
