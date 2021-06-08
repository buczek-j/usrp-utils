echo 1
sshpass -p wnesl ssh wines-nuc1@192.168.10.101 "cd ~/Documents/usrp-utils; ./tools/clean.sh";
echo 2
sshpass -p wnesl ssh wines-nuc2@192.168.10.102 "cd ~/Documents/usrp-utils; ./tools/clean.sh";
echo 3
sshpass -p wnesl ssh wines-nuc3@192.168.10.103 "cd ~/Documents/usrp-utils; ./tools/clean.sh";
echo 4
sshpass -p wnesl ssh wines-nuc4@192.168.10.104 "cd ~/Documents/usrp-utils; ./tools/clean.sh";
echo 5
sshpass -p wnesl ssh wines-nuc5@192.168.10.105 "cd ~/Documents/usrp-utils; ./tools/clean.sh";
echo 6
sshpass -p wnesl ssh wines-nuc6@192.168.10.106 "cd ~/Documents/usrp-utils; ./tools/clean.sh";
