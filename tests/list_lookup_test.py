from threading import  Event, Lock, Thread
from time import sleep, time
from random import randint

l4_ack = Event()
print_lock = Lock()


if __name__ == '__main__':
    a = []
    n = 10000
    l = 100
    time_taken = 0
    num=0
    
    for jj in range(l):
        for ii in range(l):
            a.append(randint(0, 128))

        for ii in range(n):
            b =randint(0, 128)
            tstart = time()
            if b in a:
                print_lock.acquire()
                a.pop(a.index(b))
                print_lock.release()
                pass
            time_taken = time_taken + (time()-tstart)
            num += 1

    print("array 'in':", time_taken/num)

    