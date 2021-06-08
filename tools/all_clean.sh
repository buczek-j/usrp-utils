echo 1
sshpass -p wnesl ssh wines-nuc4@192.168.10.104 "cd ~/Documents/usrp-utils; ./tools/clean.sh";
echo 2
sshpass -p wnesl ssh wines-nuc9@192.168.10.109 "cd ~/Documents/usrp-utils; ./tools/clean.sh";
echo 3
sshpass -p wnesl ssh wines-nuc6@192.168.10.106 "cd ~/Documents/usrp-utils; ./tools/clean.sh";
echo 4
sshpass -p wnesl ssh wines-nuc7@192.168.10.107 "cd ~/Documents/usrp-utils; ./tools/clean.sh";
echo 5
sshpass -p wnesl ssh wines-nuc8@192.168.10.108 "cd ~/Documents/usrp-utils; ./tools/clean.sh";
echo 6
sshpass -p wnesl ssh wines-nuc10@192.168.10.110 "cd ~/Documents/usrp-utils; ./tools/clean.sh";
