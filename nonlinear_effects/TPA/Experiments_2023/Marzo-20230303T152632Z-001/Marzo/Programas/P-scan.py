import serial, time
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from opto import Opto
import os
import sys

#Configuración de P-scan

print("Introduzca número de la toma de datos")
dato = input()          # Número del dato tomado, afecta tanto el gráfico como el txt
puntos= 3               # Número de puntos que se toman para promediar y entregar una medida
corrientes = [0, 84]    # Corrientes que se usarán en la EFTL
paso0 = 0               # A que paso se le considera el cero del disco (posición donde comienza a atenuar la luz)
tiempopos= 4.0          # Tiempo entre medidas que se deberá esperar

nombrearchivo = "P-scan_%s" % dato
print("Los archivos serán: "+nombrearchivo)

if os.path.exists(nombrearchivo+".txt") or os.path.exists(nombrearchivo+".png"):
    sys.exit("Error! : Los archivos ya existen")

class stepmotorclass:
    def __init__(self, serial_object):
        self.serial = serial_object
        self.serial.write("cpos\n".encode('utf-8'))
        self.pos = self.serial.readline()
    def cero(self):
        self.mover_a(0)
        while (self.serial.readline()!=b"Ready\r\n"):
            pass
        self.pos = 0
    def mover_a(self, grados):
        print("Moviendo a: "+str(grados))
        self.serial.write(("M "+str(grados)+"\n").encode('utf-8'))
        #print(self.serial.readline())
        while (self.serial.readline()!=b"Ready\r\n"):
            pass
        self.pos = grados
    def calibracion(self):
        self.serial.write(("calib\n").encode('utf-8'))
        while (self.serial.readline()!=b"Ready\r\n"):
            pass
        self.pos = 0
    def posicion(self):
        self.serial.write("cpos\n".encode('utf-8'))
        print(self.serial.readline())

def change_curr(x):  #Regresa a la posición "inicial" antes de buscar una nueva
    o.current(0)
    time.sleep(1.0)     #Tiempo "pre" Previo
    o.current(x)

def leer():
    lockin.write(b"Q\r")
    lectura = lockin.readline()
    return float(lectura[:-4])

#Iniciación comunicaciones seriales
o = Opto(port='COM3')
o.connect()

lockin = serial.Serial(port = 'COM5', baudrate = 9600, stopbits=1, timeout=0.1)
serial_stepmotor = serial.Serial("COM6", 9600, timeout = 1.0)
time.sleep(2) # Necesario para permitir inicializar al Arduino

stepmotor = stepmotorclass(serial_stepmotor) #Instanciación del objeto que maneja el motor paso a paso

try:
    print("Calibrando")
    stepmotor.calibracion()

    #posiciones = np.arange(0, 201, 5)
    #posiciones = np.arange(0, 2048, 10)
    #posiciones = np.ones(500)*100
    posiciones = np.append(np.arange(0, 400, 10), np.arange(400, 900, 50))

    df = pd.DataFrame(index=posiciones)

    for curr in corrientes:
        change_curr(curr)
        time.sleep(5)

        datos = np.empty([0,2])
        for grado in posiciones:
            stepmotor.mover_a(grado)
            time.sleep(tiempopos)
            Rx = 0
            for _ in range(puntos):  #Promedio
                Rx = Rx + leer()
            Rx = Rx/puntos

            print("Posición: %f, valor: %f" % (grado, Rx))
            datos = np.append(datos, [[grado, Rx]], axis=0)
            plt.cla()
            plt.plot(datos[:,0], datos[:,1],'ro-')
            plt.pause(0.1)

        plt.plot(datos[:,0], datos[:,1],'ro-')
        plt.savefig(nombrearchivo+"_"+str(curr)+"mA"+".png")
        df[str(curr)+"mA"] = datos[:,1]
        
        stepmotor.calibracion()
        time.sleep(5*tiempopos)
        
    df.to_csv(nombrearchivo+".csv", float_format='%.4f', sep= "\t")
    stepmotor.mover_a(200) #Deja al disco en una posición donde se pueda devolver y no permita alta potencia sobre la muestra

except KeyboardInterrupt:
    #stepmotor.mover_a(0)
    print("Programa finalizado por petición del usuario")

finally:
    o.close(soft_close=True)
    lockin.close()
    serial_stepmotor.close()
    print("Programa finalizado")
