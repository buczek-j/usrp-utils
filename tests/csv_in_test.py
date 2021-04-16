import csv, os

if __name__ == '__main__':
    state_dir='~/Documents/usrp-utils/FromCsv/performance_data_'
    role = 'rly1'

    state_csv = open(os.path.expanduser(state_dir+role+'.csv'), 'r', newline='')
    state_reader = csv.reader(state_csv)
    n=0
    for Exp_Ind, Loc_x, Loc_y, Loc_z, TxPower, sessRate, runTime, l2Ack, l2Time, l4Ack, l4Time, rtDelay, l2TxQueue, l4TxQueue, l2Sent in state_reader:
        if Loc_y != 'Loc_y':
            if n<10:
                print(float(Loc_y))
            n+=1
