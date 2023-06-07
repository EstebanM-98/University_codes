# -*- coding: utf-8 -*-

import serial
import numpy as np
import time
import pylab as plt
import csv
from opto import Opto

board = serial.Serial(port = 'COM3',baudrate = 9600,parity=serial.PARITY_NONE,stopbits=1,xonxoff=0,timeout=0.1)
board.write(b"W 0\r")


#Iniciación comunicaciones seriales
o = Opto(port='COM4')
o.connect()
tiempopos= 1

def cambiarCorriente(x):  #Regresa a la posición "inicial" antes de buscar una nueva
    #o.current(currI)
    #time.sleep(0.5)     #Tiempo "pre" Previo
    o.current(x)
    time.sleep(tiempopos)     #Tiempo "pos" Posterior


def leer():
    board.write(b"Q\r")
    lectura=board.readline()
    return float(lectura[:-4])

kk=0
for curr in range(0,290,5):
    cambiarCorriente(curr)
    tiempo=[]
    señal=[]
    N=5
    name=29+kk
    kk+=1
    puntos=4  #puntos
    c=0
    for i in range(N):

        start_time = time.time()
        # your code 
        Rx = 0
        for xx in range(puntos):  #Promedio
            Rx = Rx +leer()

        Rx = Rx/puntos
        elapsed_time = time.time() - start_time
        tiempo.append(c+elapsed_time)
        señal.append(Rx)
        time.sleep(1) #Tiempo entre medida.
        c+=1
        
        

    data = np.column_stack([tiempo, señal])
    datafile_path = "ev_señal"+str(name)+".txt"
    np.savetxt(datafile_path , data, fmt=['%f','%f'])
    
board.close()