
sshpass -p wnesl ssh wines-nuc1@192.168.10.101 "cd ~/Documents/usrp-utils; git pull" & sshpass -p wnesl ssh wines-nuc2@192.168.10.102 "cd ~/Documents/usrp-utils; git pull" & sshpass -p wnesl ssh wines-nuc3@192.168.10.103 "cd ~/Documents/usrp-utils; git pull"
