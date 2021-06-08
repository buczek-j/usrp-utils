#!/usr/bin/env python3

'''
Object to handle ssh connections and running commands
'''

import sys
from paramiko import SSHClient, AutoAddPolicy

class SSH_Connection():
    def __init__(self, user, host, password, index, cmd=None):
        '''
        Object to facilitate SSH Connections 
        :param user: string for username to connect to via ssh
        :param host: string of host ip address to connect to via ssh
        :param password: string for password to connect with via ssh
        '''
        self.user = user
        self.host = host
        self.password = password
        self.ssh = SSHClient()
        self.ssh.set_missing_host_key_policy(AutoAddPolicy())
        self.connected = True   # bool for if connection is successful
        self.index = index
        self.cmd=cmd

        try:
            print("trying connect ", self.host, self.user, self.password)
            self.ssh.connect(self.host, username=self.user, password=self.password)
        except Exception as e:
            sys.stderr.write("SSH connection error: {0}".format(e))		
            self.connected = False
            print("failed ", self.host, self.user, self.password)
       
        if self.connected:
            print("connected ", self.host)

    def run_command(self, command):
        '''
        Method to run SSH command
        :param command: string of bash command to execute
        '''
        try:
            ssh_stdin, ssh_stdout, ssh_stderr = self.ssh.exec_command(command,  get_pty=True)
            # https://askubuntu.com/questions/837633/top-not-showing-output-over-ssh
            # https://stackoverflow.com/questions/2909481/paramiko-and-pseudo-tty-allocation
            for line in ssh_stdout:
                print(self.host,':' ,line)

        except Exception as e:
            # sys.stderr.write("SSH connection error: {0}".format(e))
            print(e)
        
    
    def __del__(self):
        '''
        Object deconstructor
        '''
        self.ssh.close()