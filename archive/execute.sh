

#!/bin/bash
# sshpass -p wnesl ssh wines-nuc1@192.168.10.101 "source ~/prefix-3.8/setup_env.sh; python3 ~/Documents/usrp-utils/UAV_Node.py --index 0" & sshpass -p wnesl ssh wines-nuc2@192.168.10.102 "python3 ~/Documents/usrp-utils/UAV_Node.py --index 1" & sshpass -p wnesl ssh wines-nuc3@192.168.10.103 "python3 ~/Documents/usrp-utils/UAV_Node.py --index 2"

num=${1:-"3"} 

for ((i=1; i<=$num; i++))
do 
    sshpass -p wnesl ssh "wines-nuc$i@192.168.10.10$i" "source ~/prefix-3.8/setup_env.sh; python3 ~/Documents/usrp-utils/UAV_Node.py --index" "$(($i-1))"
done
