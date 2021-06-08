echo 1
sshpass -p wnesl ssh wines-nuc1@192.168.10.101 "killall python3; python3 ~/Documents/usrp-utils/tools/land.py";
echo 2
sshpass -p wnesl ssh wines-nuc2@192.168.10.102 "killall python3; python3 ~/Documents/usrp-utils/tools/land.py";
echo 3
sshpass -p wnesl ssh wines-nuc3@192.168.10.103 "killall python3; python3 ~/Documents/usrp-utils/tools/land.py";
echo 4
sshpass -p wnesl ssh wines-nuc4@192.168.10.104 "killall python3; python3 ~/Documents/usrp-utils/tools/land.py";
echo 5
sshpass -p wnesl ssh wines-nuc5@192.168.10.105 "killall python3; python3 ~/Documents/usrp-utils/tools/land.py";
echo 6
sshpass -p wnesl ssh wines-nuc6@192.168.10.106 "killall python3; python3 ~/Documents/usrp-utils/tools/land.py";
