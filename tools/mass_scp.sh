# ./mass_scp.sh "./random" "~/Documents"

echo 1
scp -r $1 wines-nuc1@192.168.10.101:$2;
echo 2
scp -r $1 wines-nuc2@192.168.10.102:$2;
echo 3
scp -r $1 wines-nuc3@192.168.10.103:$2;
echo 4
scp -r $1 wines-nuc4@192.168.10.104:$2;
echo 5
scp -r $1 wines-nuc5@192.168.10.105:$2;
echo 6
scp -r $1 wines-nuc6@192.168.10.106:$2;
