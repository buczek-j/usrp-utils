echo 1
sshpass -p wnesl ssh wines-nuc4@192.168.10.104 $1;
echo 2
sshpass -p wnesl ssh wines-nuc9@192.168.10.109 $1;
echo 3
sshpass -p wnesl ssh wines-nuc6@192.168.10.106 $1;
echo 4
sshpass -p wnesl ssh wines-nuc7@192.168.10.107 $1;
echo 5
sshpass -p wnesl ssh wines-nuc8@192.168.10.108 $1;
echo 6
sshpass -p wnesl ssh wines-nuc10@192.168.10.110 $1;
