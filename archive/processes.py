#!/usr/bin/env python3

'''
Program to launch Nodes
'''

# global libraries

from time import sleep, time
from threading import Thread
from subprocess import Popen, PIPE, run

# local libraries

wifi_ip_list = ['192.168.10.101', '192.168.10.102', '192.168.10.103']    #, '192.168.10.104', '192.168.10.105', '192.168.10.106']
username_list = ['wines-nuc1', 'wines-nuc2', 'wines-nuc3', 'wines-nuc4', 'wines-nuc5', 'wines-nuc6']
pwrd_list = ['wnesl', 'wnesl', 'wnesl', 'wnesl', 'wnesl', 'wnesl']

def main():
    '''
    Main execution method
    '''
    CMD = 'bash ; python3 ~/Documents/usrp-utils/UAV_Node.py --index '
    processes = []

    sleep(1)

    try:
        for ii in range(len(wifi_ip_list)):
            # processes.append(Popen(['source', '~/prefix-3.8/setup_env.sh;', 'python3', '~/Documents/usrp-utils/UAV_Node.py', '--index', str(ii)],stdout=PIPE, stderr=PIPE))
            # cmd = ['sshpass', '-p', 'wnesl', 'ssh', str(username_list[ii])+'@'+str(wifi_ip_list[ii]), '"source ~/prefix-3.8/setup_env.sh;', 'python3', '~/Documents/usrp-utils/UAV_Node.py', '--index', str(ii), '"']
            cmd = ['sshpass', '-p', 'wnesl', 'ssh', str(username_list[ii])+'@'+str(wifi_ip_list[ii]), 'ls']
            print(cmd)
            processes.append(Popen(cmd))
        print('RUNNING ALL PROCESSES')
        
        start_time = time()
        while time()-start_time<600:
            print('. . .')
            sleep(5)


    except Exception as e:
        print(e)

    finally:
        for proc in processes:
            try:
                proc.kill()
            except:
                pass
        print('Clossed Processes')

        print("Execution Terminated")
        
if __name__ == '__main__':
    main()