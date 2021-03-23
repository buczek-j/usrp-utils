
sshpass -p wnesl ssh wines-nuc1@192.168.10.101 "python3 ~/Documents/usrp-utils/UAV_Node.py --index 0" & sshpass -p wnesl ssh wines-nuc2@192.168.10.102 "python3 ~/Documents/usrp-utils/UAV_Node.py --index 1" & sshpass -p wnesl ssh wines-nuc3@192.168.10.103 "python3 ~/Documents/usrp-utils/UAV_Node.py --index 2"
