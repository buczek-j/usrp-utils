#!/usr/bin/env python3

'''
Program to launch Nodes
'''

# global libraries

from time import sleep
from threading import Thread

# local libraries

from Utils.SSH_Connection import SSH_Connection

# wifi_ip_list = ['192.168.10.101', '192.168.10.102', '192.168.10.103', '192.168.10.104', '192.168.10.105', '192.168.10.106']
# username_list = ['wines-nuc1', 'wines-nuc2', 'wines-nuc3', 'wines-nuc4', 'wines-nuc5', 'wines-nuc6']
# pwrd_list = ['wnesl', 'wnesl', 'wnesl', 'wnesl', 'wnesl', 'wnesl']

wifi_ip_list = ['192.168.10.104',  '192.168.10.106']
username_list = [ 'wines-nuc4', 'wines-nuc6']
pwrd_list = ['wnesl', 'wnesl']

def main():
    '''
    Main execution method
    '''
    # CMD = 'source ~/prefix-3.8/setup_env.sh; python3 ~/Documents/usrp-utils/UAV_Node.py --wait n --fly_drone n --use_radio n --index '
    CMD = 'source ~/prefix-3.8/setup_env.sh; python3 ~/Documents/usrp-utils/execute_test.py'
    ssh_connections = []
    threads = []
    stop_threads=False

    for ii in range(len(wifi_ip_list)):
        ssh_connections.append(SSH_Connection(username_list[ii], wifi_ip_list[ii], pwrd_list[ii], ii))
    
    for connection in ssh_connections:
        if connection.connected == False:
            print("Error in SSH conneciton")
            exit(0)
    sleep(1)

    try:
        for connection in ssh_connections:
            # threads.append(Thread(target=connection.run_command, args=(CMD + str(connection.index),)))
            threads.append(Thread(target=connection.run_command, args=(CMD, lambda : stop_threads)))
        
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
            connection.run_command('killall python3')
        sleep(0.5)
        print("Execution Terminated")
        
if __name__ == '__main__':
    main()