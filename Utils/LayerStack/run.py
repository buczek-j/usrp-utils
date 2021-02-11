from OFDM_Tx import OFDM_Tx
import time, threading

class run_thread(threading.Thread):
    def __init__(self, tb):
        threading.Thread.__init__(self)
        self.setDaemon(1)
        self.tb = tb
        self.done = False
        self.start()

    def run(self):
        while not self.done:
            try:
                self.tb.handle_msg("h"*180)
            except KeyboardInterrupt:
                self.done = True


layer1_tx = OFDM_Tx()
thread = run_thread(layer1_tx)

try: 
    layer1_tx.run()
except KeyboardInterrupt:
    thread.done = True
    thread = None
