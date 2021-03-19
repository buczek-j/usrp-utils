#!/usr/bin/env python3

'''
Program to automate the generation  of the locations and radio gains for each scenario 
and save the data into csv formatting
'''

import csv
from numpy import arange

def main():
    '''
    '''
    # TX Gains to test
    dest1_tx_gains = [0.8]
    rly1_tx_gains = [0.8]#arange(0.5, 1.0, 0.1)
    src1_tx_gains = [0.8]
    dest2_tx_gains = [0.8]
    rly2_tx_gains = [0.8]#arange(0.5, 1.0, 0.1)
    src2_tx_gains = [0.8]

    # RX Gains to test
    dest1_rx_gains = [0.8]
    rly1_rx_gains = [0.8]
    src1_rx_gains = [0.8]
    dest2_rx_gains = [0.8]
    rly2_rx_gains = [0.8]
    src2_rx_gains = [0.8]

    # Locations to test
    dest1_locs = [[0.0,1.0]]

    rly1_locs = [[5.0, 5.0], [5.0, 6.0], [5.0, 7.0]]
    #rly1_locs = []
    # for x in arange(-5.0, 6.0, 1.0):
    #     for y in arange(-5.0, 6.0, 1.0):
    #         rly1_locs.append([x,y])

    src1_locs = [[5.0,10.0]]

    dest2_locs = [[0.0,1.0]]

    rly2_locs = [[6.0, 5.0], [6.0, 6.0], [6.0, 7.0]]
    #rly2_locs = []
    # for x in arange(-5.0, 6.0, 1.0):
    #     for y in arange(-5.0, 6.0, 1.0):
    #         rly2_locs.append([x,y])

    src2_locs = [[5.0,10.0]]

    # Altitudes 
    dest1_alt = -5.0
    rly1_alt = -5.0
    src1_alt = -5.0

    dest2_alt = -5.0
    rly2_alt = -5.0
    src2_alt = -5.0
    
    with open('test_config.csv', 'w', newline='') as csvfile:
        fieldnames = ['test_index', 'dest1', 'rly1', 'src1', 'dest2', 'rly2', 'src2']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        # iterate through all locations (prioritize relays)
        test_counter = 0
        for dest1_loc in dest1_locs:
            for src1_loc in src1_locs:
                for dest2_loc in dest2_locs:
                    for src2_loc in src2_locs:
                        for rly1_loc in rly1_locs:
                            for rly2_loc in rly2_locs:
                                # check for intersections
                                if rly2_loc not in [rly1_loc, dest1_loc, src1_loc, dest2_loc, src2_loc] and rly1_loc not in [rly2_loc, dest1_loc, src1_loc, dest2_loc, src2_loc]:
                                    # iterate through all gains
                                    for dest1_tx_gain in dest1_tx_gains:
                                        for dest1_rx_gain in dest1_rx_gains:
                                            for src1_tx_gain in src1_tx_gains:
                                                for src1_rx_gain in src1_rx_gains:
                                                    for dest2_tx_gain in dest2_tx_gains:
                                                        for dest2_rx_gain in dest2_rx_gains:
                                                            for src2_tx_gain in src2_tx_gains:
                                                                for src2_rx_gain in src2_rx_gains:
                                                                    for rly1_tx_gain in rly1_tx_gains:
                                                                        for rly1_rx_gain in rly1_rx_gains:
                                                                            for rly2_tx_gain in rly2_tx_gains:
                                                                                for rly2_rx_gain in rly2_rx_gains:
                                                                                    writer.writerow({
                                                                                        'test_index':str(test_counter), 
                                                                                        'dest1':str(dest1_loc[0]) + ':' + str(dest1_loc[1]) + ':' + str(dest1_alt) + ':' + str(round(dest1_rx_gain,2)) + ':' + str(round(dest1_tx_gain,2)),
                                                                                        'rly1':str(rly1_loc[0]) + ':' + str(rly1_loc[1]) + ':' + str(rly1_alt) + ':' + str(round(rly1_rx_gain,2)) + ':' + str(round(rly1_tx_gain,2)),
                                                                                        'src1':str(src1_loc[0]) + ':' + str(src1_loc[1]) + ':' + str(src1_alt) + ':' + str(round(src1_rx_gain,2)) + ':' + str(round(src1_tx_gain,2)),
                                                                                        'dest2':str(dest2_loc[0]) + ':' + str(dest2_loc[1]) + ':' + str(dest2_alt) + ':' + str(round(dest2_rx_gain,2)) + ':' + str(round(dest2_tx_gain,2)),
                                                                                        'rly2':str(rly2_loc[0]) + ':' + str(rly2_loc[1]) + ':' + str(rly2_alt) + ':' + str(round(rly2_rx_gain,2)) + ':' + str(round(rly2_tx_gain,2)),
                                                                                        'src2':str(src2_loc[0]) + ':' + str(src2_loc[1]) + ':' + str(src2_alt) + ':' + str(round(src2_rx_gain,2)) + ':' + str(round(src2_tx_gain,2)),
                                                                                    })
                                                                                    test_counter += 1
                                                                

if __name__ == '__main__':
    main()