from iUSBDAQ import iUSBDAQ

import numpy as np
import matplotlib.pyplot as plt
from threading import Thread, Lock, Event
import time

bufflen = 1000
buff = np.zeros((bufflen, NCHANNELS), np.float)
buffidx = 0

def read(lock, stop):
    global buff, buffidx
    dev = iUSBDAQ(0)
    dev.AIStartStream()

    while not stop.isSet():
        dev.AIGetScans()
        with lock:
            buff[buffidx,:] = dev.buff[-NCHANNELS:]
            buffidx = (buffidx + 1) % bufflen

    dev.AIStopStream()

def draw(lock, stop):
    plt.ion()
    plt.figure()
    lines = plt.plot(buff)
    # ratio = plt.plot(buff[:,1])[0]
    bar = plt.plot([0,0],[0,5])[0]
    # plt.ylim([2.5,2.6])
    plt.ylim([0,5])
    plt.ylabel('Voltage')

    while not stop.isSet():
        with lock:
            for i, line in enumerate(lines):
                line.set_ydata(buff[:,i])
            # ratio.set_ydata(buff[:,1] * 2.533 / buff[:,2])
            bar.set_xdata([buffidx, buffidx])

            # rat = buff[:,1] + 2.580 - buff[:,2]
            rat = buff[:,1]
        avg = np.mean(rat)
        rmse = np.sqrt(np.mean(np.power(rat - avg, 2)))
        vpp = np.max(rat) - np.min(rat)

        print avg, rmse, vpp
        plt.draw()

    plt.close()

if __name__ == '__main__':
    assert iUSBDAQ.EnumerateDev() >= 1

    lock = Lock()
    stop = Event()
    reader = Thread(target=read, args=(lock, stop))
    drawer = Thread(target=draw, args=(lock, stop))

    reader.start()
    drawer.start()

    time.sleep(30)
    stop.set()

    reader.join()
    drawer.join()
