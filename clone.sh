#!/bin/bash

echo 1
sudo rsync -avv -e ssh ~/Documents/usrp-utils/ wines-nuc4@192.168.10.104:~/Documents/usrp-utils/
echo 2
sudo rsync -avv -e ssh ~/Documents/usrp-utils/ wines-nuc9@192.168.10.109:~/Documents/usrp-utils/
echo 3
sudo rsync -avv -e ssh ~/Documents/usrp-utils/ wines-nuc6@192.168.10.106:~/Documents/usrp-utils/
echo 4
sudo rsync -avv -e ssh ~/Documents/usrp-utils/ wines-nuc7@192.168.10.107:~/Documents/usrp-utils/
echo 5
sudo rsync -avv -e ssh ~/Documents/usrp-utils/ wines-nuc8@192.168.10.108:~/Documents/usrp-utils/
echo 6
sudo rsync -avv -e ssh ~/Documents/usrp-utils/ wines-nuc10@192.168.10.110:~/Documents/usrp-utils/

# scp -r ~/Documents/usrp-utils wines-nuc3@192.168.10.103:~/Documents;

