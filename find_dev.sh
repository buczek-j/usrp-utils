echo 1
sshpass -p wnesl ssh wines-nuc1@192.168.10.101 "uhd_find_devices "
echo 2
sshpass -p wnesl ssh wines-nuc2@192.168.10.102 "uhd_find_devices "
echo 3
sshpass -p wnesl ssh wines-nuc3@192.168.10.103 "uhd_find_devices "
echo 4
sshpass -p wnesl ssh wines-nuc4@192.168.10.104 "uhd_find_devices "
echo 5
sshpass -p wnesl ssh wines-nuc5@192.168.10.105 "uhd_find_devices "
echo 6
sshpass -p wnesl ssh wines-nuc6@192.168.10.106 "uhd_find_devices "
