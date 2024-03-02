# -*- coding: utf-8 -*-
"""
Created on Wed Jun 15 10:50:12 2022

@author: elgar
"""

#from opto import Opto
import serial
import numpy as np
import time
import matplotlib.pyplot as plt
import os
import sys
from scipy.optimize import curve_fit
import pandas as pd
import statsmodels.api as sm



def r_sqr(datexp,dataj):
    #Función para criterio de R^2
    return 1-sum((datexp-dataj)**2)/sum((datexp-np.mean(datexp))**2)


def ajuste(x,m, b):
    # Función de ajuste lineal
    return m*(x)+b

def leer():
    # Función que permite leer los valores del Lock-in
    board.write(b"Q\r")
    lectura=board.readline()
    return float(lectura[:-4])

# Esta clase permite controlar el servo-motor una vez se ha leido el puerto
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
#board.reset_input_buffer()


#o = Opto(port='COM3')
#o.connect()

nombrearchivo = "Verificar_linealidad" #Nombre de archivo
board = serial.Serial(port = 'COM5',baudrate = 9600,parity=serial.PARITY_NONE,stopbits=1,xonxoff=0,timeout=0.1) #Lectura puerto Lock-in
serial_stepmotor = serial.Serial("COM6", 9600, timeout = 5.0) # Lectura puerto arduino
time.sleep(2) # Necesario para permitir inicializar al Arduino
stepmotor = stepmotorclass(serial_stepmotor) #Inicializiación del objeto clase stepmotorclass
tiempoo=4 #Tiempo de espera entre la orden de mover el disco y tomar los valores del Lock-in en segundos


# Rango de toma de datos del disco en paso.
a=float(input('Ingrese limite inferior del paso del disco :'))#Limite inferior)
b=float(input('Ingrese limite superior del paso del disco :')) #Limite superior
n=float(input('Ingrese cantidad de pasos:')) # Número de datos entre este rango

try:

    stepmotor.calibracion() #Calibrar siempre antes de verificar linealidad
    voltaje=[] #Lista con voltajes promediados por paso en el Lock-in
    puntos=3 # Número de datos a promediar en la lectura del voltaje del Lock-in
    rango=np.arange(a,b+1,(b-a)/n)
            
    for i in rango:
        
        stepmotor.mover_a(round(i,3)) 
        time.sleep(tiempoo) #Delay execution for a given number of seconds
        Rx = 0
        for xx in range(puntos):  #Promedio
            Rx = Rx + leer()
            
        Rx = Rx/puntos
        
        print(Rx)
        voltaje.append(round(Rx,3))
        
    
except KeyboardInterrupt:
    print('a')

        
finally:
    #o.close(soft_close=True)
    board.close()
    serial_stepmotor.close()
    print("Programa finalizado")
    
voltaje=np.array(voltaje)
voltaje = voltaje/np.max(voltaje)
voltaje = np.log10(1/voltaje)
pasos=rango

# Para que la función tenga sentido x se tiene que dar en grados.
# Cómo originalmente son pasos se usa la siguiente relación
deltaAng = 360/2051
angM = 21 # paso para mínima potencia, máxima ND
ang1 = 310 - (pasos-angM)*deltaAng # Conversión de pasos a grados

nombrearchivo = "Verificar_linealidad"
d= {'angulo': ang1 , 'Voltaje': voltaje}
df = pd.DataFrame(data=d)
df.to_csv(nombrearchivo+".txt", float_format='%.4f', sep= "\t")

popt, cov2  = curve_fit(ajuste, ang1, voltaje)

w2_ajuste1 = ajuste(ang1, *popt)

plt.rcParams['figure.figsize'] = 14, 7 # para modificar el tamaño de la figura
font = {'weight' : 'bold', 'size'   : 18}

fig1 = plt.figure(1)
ax1 = plt.subplot(1,2,1)

#plt.title('Ajsute lineal para 6722B', fontsize = '14')
ax1.plot(ang1, voltaje, 'o', color = 'darkblue',label='Lock-in')
ax1.plot(ang1, w2_ajuste1, '-.', color = 'red',label='Ajuste')
plt.xlabel('ángulo (°)', fontsize = '14')
plt.ylabel(r'log$_{10}(1/T)$', fontsize = '14')
plt.grid()
plt.legend()
plt.show()
plt.savefig(nombrearchivo+".png")

print('El coeficiene de determinación asociado al ajuste es: R^2 = ', round(r_sqr(voltaje,w2_ajuste1),5)) #Coeficiente R^2
print('Diferencia de %.1f %%'%(100*abs(abs(popt[0])-0.0108)/0.0108))


#create dataset
df = pd.DataFrame ({'x':ang1,
                   'y': voltaje})

#fit simple linear regression model
y = df['y']
x = df[['x']]
x = sm.add_constant(x)
model = sm.OLS(y, x).fit()

#view model summary
print(model.summary())

#produce residual plots
fig = plt.figure(figsize=(12,8))
fig = sm.graphics.plot_regress_exog(model, 'x', fig=fig)

#produce Q-Q plot
res = model.resid
fig = sm.qqplot(res, fit=True, line="45")
plt.show()


    