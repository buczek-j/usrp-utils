#!/bin/bash
# ./mass_scp.sh "./random" "~/Documents"

echo 1
scp -r $1 wines-nuc4@192.168.10.104:$2;
echo 2
scp -r $1 wines-nuc9@192.168.10.109:$2;
echo 3
scp -r $1 wines-nuc6@192.168.10.106:$2;
echo 4
scp -r $1 wines-nuc7@192.168.10.107:$2;
echo 5
scp -r $1 wines-nuc8@192.168.10.108:$2;
echo 6
scp -r $1 wines-nuc10@192.168.10.110:$2;
