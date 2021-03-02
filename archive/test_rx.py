from optparse import OptionParser
from gnuradio.eng_option import eng_option
from gnuradio import digital
import benchmark_rx_narrow, benchmark_tx_narrow
import transmit_path_narrow, receive_path_narrow, uhd_interface_narrow
def rx_callback(ok, received_pkt):		
    success = 0
    success = ok
    print(received_pkt)
		
			
def start_l1_receiving_block(options):
    l1_transmission_block = benchmark_rx_narrow.my_top_block(mods[options.modulation], rx_callback, options)
    l1_transmission_block.start()
    l1_transmission_block.wait()


if __name__ == '__main__':
    parser = OptionParser(option_class=eng_option, conflict_handler="resolve")
    expert_grp = parser.add_option_group("Expert")  

    parser.add_option("-M", "--megabytes", type="eng_float", default=1.0,
                        help="set megabytes to transmit [default=%default]")

    parser.add_option("","--to-file", default=None,
                        help="Output file for modulated samples")
    parser.add_option("", "--tx-gain", type="eng_float", default= 20,
                        help="set tx gain [default=%default]")
    parser.add_option("", "--rx-gain", type="eng_float", default= 30,
                        help="set rx gain [default=%default]")
    parser.add_option("", "--freq", type="float", default= 2.4e9,
                        help="frequency (Hz) [default=%default]")
    parser.add_option("-m", "--modulation", type="string", default='gfsk', help="Select modulation")
   
    mods = digital.modulation_utils.type_1_mods()
    demods = digital.modulation_utils.type_1_demods()

    for mod in mods.values():
        mod.add_options(expert_grp)	

    for mod in demods.values():
        mod.add_options(expert_grp)			

    # tx parser
    transmit_path_narrow.transmit_path.add_options(parser, expert_grp)
    uhd_interface_narrow.uhd_transmitter.add_options(parser)

    # rx parser
    receive_path_narrow.receive_path.add_options(parser, expert_grp)
    uhd_interface_narrow.uhd_receiver.add_options(parser)
		
    (options, args) = parser.parse_args ()

    start_l1_receiving_block(options)


    