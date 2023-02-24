import time
import serial
import numpy as np
import desplazadorL as dp
from opto import Opto
import matplotlib.pyplot as plt
import os
import sys

#Configuración de Z-scan

print("Introduzca número de la toma de datos")
dato = input()  #Número del dato tomado, afecta tanto el gráfico como el txt
centini = 0     #Desde qué centímetros se moverá
centm = 16      #Hasta cuál centímetros se moverá
corriente = 50  #Corriente que se usará
puntos = 3      #Cantidad de tomas a promediar para obtener una medida
tiempopos= 4

nombrearchivo = "Z-scan_%dmA_%s" % (corriente, dato)
print("Los archivos serán: "+nombrearchivo)

if os.path.exists(nombrearchivo+".txt") or os.path.exists(nombrearchivo+".png"):
    sys.exit("Error! : Los archivos ya existen")

def change_curr(x):  #Regresa a la posición "inicial" antes de buscar una nueva
    o.current(0)
    time.sleep(1.0)     #Tiempo "pre" Previo
    o.current(x)

#Iniciación comunicaciones seriales
o = Opto(port='COM3')
o.connect()

pts=dp.detectar()
print(pts)

# Seleccionar el puerto correspondiente al Desplazador
desp1,info1=dp.abrirpuertos("COM7")

#Inicializa el objeto desplazador con su correspondiente serial
control_d=dp.desplazador(desp1, 17)

# Lectura valor de transmisión Lock-in
board = serial.Serial(port = 'COM5', baudrate = 9600, stopbits=1, timeout=0.1)

board.write(b"W 0\r")

def leer():
    board.write(b"Q\r")
    lectura = board.readline()
    return float(lectura[:-4])

data=np.empty([0,2])
change_curr(corriente)
try:
    dp.cero(desp1)
    for nueva_pos in range(centini*10*200,centm*10*200,5*100):
        print("________________\n")
        control_d.cambiar_pos(nueva_pos)
        time.sleep(tiempopos)
        Rx = 0
        for xx in range(puntos):  #Promedio
            Rx = Rx + leer()
        Rx = Rx/puntos
        print("Posición: %f, valor: %f" % (nueva_pos/200.0, Rx))
        data=np.append(data,[[nueva_pos/200.0,Rx]],axis=0)
        plt.cla()
        plt.plot(data[:,0],data[:,1],'ro-')
        plt.pause(0.1)
    np.savetxt(nombrearchivo +".txt", data, fmt='%.4f')
    plt.plot(data[:,0],data[:,1],'ro-')
    plt.title("Z-scan %d mA" % corriente)
    plt.xlabel("Longitud desplazamiento [mm]")
    plt.ylabel("Voltaje Lock-in [V]")
    plt.savefig(nombrearchivo +".png")
    print("Diferencia max-min: %f \n Diferencia relativa: %f"% (data[:,1].max()-data[:,1].min(), (data[:,1].max()-data[:,1].min())/data[:,1].max()))
    print("Desv Est %f" % data[:,1].std())

except KeyboardInterrupt:
    print("Programa terminado")

finally:
    o.close(soft_close=True)
    board.close()
    desp1.close()
