import csv
from time import time

row_list = ["Iteration Number","Node0 Loc", "Node1 Loc", "Node2 Loc", "Node3 Loc", "Node4 Loc", "Node5 Loc", "Node0 Tx Gain", "Node1 Tx Gain", "Node2 Tx Gain", "Node3 Tx Gain", "Node4 Tx Gain", "Node5 Tx Gain", "Number L4 Acks"]
class Writer():
    def __init__(self):
        self.f =  open('test_csv.csv', 'a', newline='') 
        self.writer = csv.writer(self.f)
        self.writer.writerow(row_list)

    def run(self):

        # 0.0003342628479003906
        # while True:
        #     msg = input("msg: ")
        #     time_start = time()
        #     with open('test_csv.csv', 'a', newline='') as file:
        #         self.writer = csv.writer(file)
        #         self.writer.writerow([msg])
        #     print(time()-time_start)

        # 4.887580871582031e-05
        # with open('test_csv.csv', 'a', newline='') as file:
        #     writer = csv.writer(file)
        #     while True:
        #         msg = input("msg: ")
        #         time_start = time()
        #         writer.writerow([msg])
        #         print(time()-time_start)

        # 1.52587890625e-05
        while True:
            msg = input("msg: ")
            time_start = time()
            self.writer.writerow([msg])
            print(time()-time_start)

if __name__ == '__main__':
    my_writer = Writer()
    my_writer.run()