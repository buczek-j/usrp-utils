# user made libraries
from LayerStack import Control_Plane, Layer1, Layer2, Layer3, Layer4, Network_Layer
from threading import Thread
from subprocess import Popen, PIPE, DEVNULL, TimeoutExpired
from signal import SIGTERM
from os import killpg, _exit, getpgid
from time import sleep
import psutil

def rtn_False():
    return False


def kill(proc_pid):
    process = psutil.Process(proc_pid)
    for proc in process.children(recursive=True):
        proc.kill()
    process.kill()

layer1 = Layer1.Layer1(debug=False)
layer1.init_layers(upper=None, lower=None)
threads = {}


for layer in [layer1]:
    threads[layer.layer_name + "_pass_up"] = Thread(target=layer.pass_up, args=(lambda : rtn_False,))
    threads[layer.layer_name + "_pass_down"] = Thread(target=layer.pass_down, args=(lambda : rtn_False,))
    threads[layer.layer_name + "_pass_up"].start()
    threads[layer.layer_name + "_pass_down"].start() 


proc = Popen('python3 LayerStack/L1_protocols/TRX_ODFM_USRP.py '+str('--serial "" --rx_bw 500000 --rx_freq 2500000000 --rx_gain 0.6 --tx_bw 500000 --tx_freq 2700000000 --tx_gain 0.8 --input_port "55555" --output_port "55556"'), stdout=PIPE, shell=True)

sleep(10)

print("INIT")

kill(proc.pid)

print('Killed')

proc = Popen('python3 LayerStack/L1_protocols/TRX_ODFM_USRP.py '+str('--serial "" --rx_bw 500000 --rx_freq 2500000000 --rx_gain 0.8 --tx_bw 500000 --tx_freq 2700000000 --tx_gain 0.8 --input_port "55555" --output_port "55556"'), stdout=PIPE, shell=True)

sleep(50)