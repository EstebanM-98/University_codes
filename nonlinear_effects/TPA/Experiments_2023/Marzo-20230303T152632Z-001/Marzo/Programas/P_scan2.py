# -*- coding: utf-8 -*-
"""
Created on Wed Jul 13 08:55:07 2022

@author: elgar
"""

import serial, time
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from opto import Opto
import os
import sys

#Configuración de P-scan

os.chdir('../')
path=os.getcwd()
print("Introduzca número de la toma de datos")
dato = input()          # Número del dato tomado, afecta tanto el gráfico como el txt
puntos= 3               # Número de puntos que se toman para promediar y entregar una medida
corrientes = [290, 80]  # Corrientes que se usarán en la EFTL: Desenfocado, enfocado.
paso0 = 0               # A que paso se le considera el cero del disco (posición donde comienza a atenuar la luz)
tiempopos= 4.0          # Tiempo entre medidas que se deberá esperar

nombrearchivo = "\\P-scan_%s" % dato
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

#Cambia de corriente y lee el valor actual de voltaje.
def curr_leer(c):
    change_curr(c)
    time.sleep(5)
    Rx = 0
    
    for _ in range(puntos):  #Promedio
        Rx = Rx + leer()
        Rx = Rx/puntos
        
    return Rx
    

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
    
    v1=[] #Voltajes para la corriente desenfocada.
    
    v2=[] #Voltajes para la corriente enfocada.

    #posiciones = np.arange(0, 201, 5)
    #posiciones = np.arange(0, 2048, 10)
    #posiciones = np.ones(500)*100
    
    #Rango de pasos del disco.
    posiciones = np.append(np.arange(350, 400, 10), np.arange(400, 1100, 50))

    df = pd.DataFrame(index=posiciones)

  
    for grado in posiciones:
        
        stepmotor.mover_a(grado)
        
        time.sleep(tiempopos)
        
        v1.append(curr_leer(corrientes[0]))
        
        v2.append(curr_leer(corrientes[1]))
       

        
    df[str(corrientes[0])+"mA"] = v1
    
    df[str(corrientes[1])+"mA"] = v2
    
    
        
    stepmotor.calibracion()
    
    time.sleep(5*tiempopos)
    
    plt.plot(posiciones,v1,'k',label="corriente "+str(corrientes[0])+"mA")
    
   # plt.savefig(path+'Desenfocado_pscan2_'+dato +".png")    
    plt.plot(posiciones,v2,'r',label="corriente "+str(corrientes[1])+"mA")
    
    plt.xlabel('Paso')
    plt.ylabel( "Voltaje Lock-in")
    plt.legend()
        
    df.to_csv(path+nombrearchivo+".txt", float_format='%.4f', sep= "\t")
    
    plt.savefig(path+'\\Pscan2_'+dato +".png")
    
    stepmotor.mover_a(200) #Deja al disco en una posición donde se pueda devolver y no permita alta potencia sobre la muestra

except KeyboardInterrupt:
    #stepmotor.mover_a(0)
    print("Programa finalizado por petición del usuario")

finally:
    o.close(soft_close=True)
    lockin.close()
    serial_stepmotor.close()
    print("Programa finalizado")
