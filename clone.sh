#!/bin/bash

echo 1
sudo rsync -avv -e ssh ~/Documents/usrp-utils/ wines-nuc1@192.168.10.101:~/Documents/usrp-utils/
echo 2
sudo rsync -avv -e ssh ~/Documents/usrp-utils/ wines-nuc2@192.168.10.102:~/Documents/usrp-utils/
echo 3
sudo rsync -avv -e ssh ~/Documents/usrp-utils/ wines-nuc3@192.168.10.103:~/Documents/usrp-utils/
echo 4
sudo rsync -avv -e ssh ~/Documents/usrp-utils/ wines-nuc4@192.168.10.104:~/Documents/usrp-utils/
echo 5
sudo rsync -avv -e ssh ~/Documents/usrp-utils/ wines-nuc5@192.168.10.105:~/Documents/usrp-utils/
echo 6
sudo rsync -avv -e ssh ~/Documents/usrp-utils/ wines-nuc6@192.168.10.106:~/Documents/usrp-utils/

# scp -r ~/Documents/usrp-utils wines-nuc3@192.168.10.103:~/Documents;

