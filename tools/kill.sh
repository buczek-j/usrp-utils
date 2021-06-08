echo 1
sshpass -p wnesl ssh wines-nuc4@192.168.10.104 "killall python3; python3 ~/Documents/usrp-utils/tools/kill.py";
echo 2
sshpass -p wnesl ssh wines-nuc9@192.168.10.109 "killall python3; python3 ~/Documents/usrp-utils/tools/kill.py";
echo 3
sshpass -p wnesl ssh wines-nuc6@192.168.10.106 "killall python3; python3 ~/Documents/usrp-utils/tools/kill.py";
echo 4
sshpass -p wnesl ssh wines-nuc7@192.168.10.107 "killall python3; python3 ~/Documents/usrp-utils/tools/kill.py";
echo 5
sshpass -p wnesl ssh wines-nuc8@192.168.10.108 "killall python3; python3 ~/Documents/usrp-utils/tools/kill.py";
echo 6
sshpass -p wnesl ssh wines-nuc10@192.168.10.110 "killall python3; python3 ~/Documents/usrp-utils/tools/kill.py";
