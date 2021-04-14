from threading import  Event, Lock, Thread
from time import sleep, time

l4_ack = Event()
print_lock = Lock()

class printer():
    def __init__(self, window=1):
        self.a = True
        self.time = 0
        self.acks = []
        self.n_p1=0
        self.n_p2=0
        self.p1_time=0
        self.p2_time=0
        for ii in range(window):
            self.acks.append(True)
    
    def print(self, msg, index):
        while self.acks[index]:
            print_lock.acquire()
            # print(msg)
            print_lock.release()
            # sleep(0.5)
        self.p1_time= self.p1_time + (time()-self.time)
        self.n_p1+=1

    def print2(self, msg, index):
        while not globals()["l4_ack"].isSet():
            print_lock.acquire()
            # print(msg)
            print_lock.release()
            # sleep(0.5)
        self.p2_time= self.p2_time + (time()-self.time)
        self.n_p2+=1

if __name__ == '__main__':
    p = printer(2)
    
    for ii in range(10000):
        p1 = Thread(target=p.print, args=("Hello "+str(ii), 0,))
        p1.start()
        p2 = Thread(target=p.print2, args=("Hello "+str(ii), 1,))
        p2.start()
        sleep(0.001)

        p.time = time()
        p.acks[0] = False

        p.time = time()
        globals()["l4_ack"].set()

    

    print("p1:", p.p1_time/p.n_p1, " p2:", p.p2_time/p.n_p2)

    