#!/bin/bash

echo 1
scp -r ~/Documents/usrp-utils wines-nuc1@192.168.10.101:~/Documents;
echo 2
scp -r ~/Documents/usrp-utils wines-nuc2@192.168.10.102:~/Documents;
echo 3
scp -r ~/Documents/usrp-utils wines-nuc3@192.168.10.103:~/Documents;

