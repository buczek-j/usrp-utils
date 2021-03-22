#!/usr/bin/env python3

'''
Program to launch Nodes
'''

# global libraries

from time import sleep
from threading import Thread

# local libraries

from Utils.Emane_Node import wifi_ip_list, username_list, pwrd_list
from Utils.SSH_Connection import SSH_Connection

def main():
    '''
    Main execution method
    '''
    CMD = 'python3 ~/Documents/usrp-utils/Utils/UAV_Node.py --index '
    ssh_connections = []
    threads = []

    for ii in range(len(wifi_ip_list)):
        ssh_connections.append(SSH_Connection(username_list[ii], wifi_ip_list[ii], pwrd_list[ii], str(ii)))
    
    for connection in ssh_connections:
        if connection.connected == False:
            print("Error in SSH conneciton")
            exit(0)

    sleep(1)

    try:
        for connection in ssh_connections:
            threads.append(Thread(target=connection.run_command, args=(CMD + connection.index,)))
        
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