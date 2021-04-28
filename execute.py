#!/usr/bin/env python3

'''
Program to launch Nodes
'''

# global libraries

from argparse import ArgumentParser
from time import sleep
from threading import Thread

# local libraries

from Utils.SSH_Connection import SSH_Connection

wifi_ip_list = ['192.168.10.101', '192.168.10.102', '192.168.10.103', '192.168.10.104', '192.168.10.105', '192.168.10.106']
username_list = ['wines-nuc1', 'wines-nuc2', 'wines-nuc3', 'wines-nuc4', 'wines-nuc5', 'wines-nuc6']
pwrd_list = ['wnesl', 'wnesl', 'wnesl', 'wnesl', 'wnesl', 'wnesl']

main_test = [
    'source ~/prefix-3.8/setup_env.sh; python3 ~/Documents/usrp-utils/UAV_Node.py --index 0 --fly_drone n',
    'source ~/prefix-3.8/setup_env.sh; python3 ~/Documents/usrp-utils/UAV_Node.py --index 1  ',
    'source ~/prefix-3.8/setup_env.sh; python3 ~/Documents/usrp-utils/UAV_Node.py --index 2 --fly_drone n',
    'source ~/prefix-3.8/setup_env.sh; python3 ~/Documents/usrp-utils/UAV_Node.py --index 3 --fly_drone n',
    'source ~/prefix-3.8/setup_env.sh; python3 ~/Documents/usrp-utils/UAV_Node.py --index 4  ',
    'source ~/prefix-3.8/setup_env.sh; python3 ~/Documents/usrp-utils/UAV_Node.py --index 5 --fly_drone n',
]

no_tx = [
    'source ~/prefix-3.8/setup_env.sh; python3 ~/Documents/usrp-utils/UAV_Node.py --index 0 --use_tx n --fly_drone n',
    'source ~/prefix-3.8/setup_env.sh; python3 ~/Documents/usrp-utils/UAV_Node.py --index 1 --use_tx n  ',
    'source ~/prefix-3.8/setup_env.sh; python3 ~/Documents/usrp-utils/UAV_Node.py --index 2 --use_tx n --fly_drone n',
    'source ~/prefix-3.8/setup_env.sh; python3 ~/Documents/usrp-utils/UAV_Node.py --index 3 --use_tx n --fly_drone n',
    'source ~/prefix-3.8/setup_env.sh; python3 ~/Documents/usrp-utils/UAV_Node.py --index 4 --use_tx n  ',
    'source ~/prefix-3.8/setup_env.sh; python3 ~/Documents/usrp-utils/UAV_Node.py --index 5 --use_tx n --fly_drone n',
]

no_radio = [
    'source ~/prefix-3.8/setup_env.sh; python3 ~/Documents/usrp-utils/UAV_Node.py --index 0 --use_radio n --fly_drone n',
    'source ~/prefix-3.8/setup_env.sh; python3 ~/Documents/usrp-utils/UAV_Node.py --index 1 --use_radio n',
    'source ~/prefix-3.8/setup_env.sh; python3 ~/Documents/usrp-utils/UAV_Node.py --index 2 --use_radio n --fly_drone n',
    'source ~/prefix-3.8/setup_env.sh; python3 ~/Documents/usrp-utils/UAV_Node.py --index 3 --use_radio n --fly_drone n',
    'source ~/prefix-3.8/setup_env.sh; python3 ~/Documents/usrp-utils/UAV_Node.py --index 4 --use_radio n ',
    'source ~/prefix-3.8/setup_env.sh; python3 ~/Documents/usrp-utils/UAV_Node.py --index 5 --use_radio n --fly_drone n',
]

is_sim = [
    'source ~/prefix-3.8/setup_env.sh; python3 ~/Documents/usrp-utils/UAV_Node.py --index 0 --is_sim y',
    'source ~/prefix-3.8/setup_env.sh; python3 ~/Documents/usrp-utils/UAV_Node.py --index 1 --is_sim y',
    'source ~/prefix-3.8/setup_env.sh; python3 ~/Documents/usrp-utils/UAV_Node.py --index 2 --is_sim y',
    'source ~/prefix-3.8/setup_env.sh; python3 ~/Documents/usrp-utils/UAV_Node.py --index 3 --is_sim y',
    'source ~/prefix-3.8/setup_env.sh; python3 ~/Documents/usrp-utils/UAV_Node.py --index 4 --is_sim y',
    'source ~/prefix-3.8/setup_env.sh; python3 ~/Documents/usrp-utils/UAV_Node.py --index 5 --is_sim y',
]
def main(options):
    '''
    Main execution method
    '''
    if options.cmd == 'main':
        CMD = main_test
    
    elif options.cmd == 'no_tx':
        CMD = no_tx

    elif options.cmd == 'no_radio':
        CMD = no_radio
    else:
        CMD = is_sim
    

    ssh_connections = []
    threads = []
    stop_threads=False

    for ii in range(len(wifi_ip_list)):
        ssh_connections.append(SSH_Connection(username_list[ii], wifi_ip_list[ii], pwrd_list[ii], ii, CMD[ii]))
    
    for connection in ssh_connections:
        if connection.connected == False:
            print("Error in SSH conneciton")
            exit(0)
    sleep(1)

    try:
        for connection in ssh_connections:
            threads.append(Thread(target=connection.run_command, args=(connection.cmd + options.global_home,)))
        
        for thread in threads:
            thread.start()
            sleep(0.2)

        sleep(600)

    except Exception as e:
        print(e)

    finally:
        for thread in threads:
            try:
                thread._Thread__stop()	
            except:
                pass
        print('Clossed Threads')

        for connection in ssh_connections:
            connection.run_command('killall python3', )
        sleep(0.5)
        print("Execution Terminated")
        

def arguments_parser():
    parser = ArgumentParser()
    parser.add_argument('--cmd', type=str, default='', help='cmd to run')
    parser.add_argument('--global_home', type=str, default='', help='global lat/lon origin')
    return parser.parse_args()

if __name__ == '__main__':
    options = arguments_parser()
    
    main(options)

    