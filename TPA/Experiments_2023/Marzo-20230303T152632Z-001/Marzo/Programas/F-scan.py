from opto import Opto
import serial
import numpy as np
import time
import matplotlib.pyplot as plt
import os
import sys

#Configuración de F-scan57

path=os.getcwd()

print("Introduzca número de la toma de datos")
dato = input()  #Número del dato tomado, afecta tanto el gráfico como el txt
dobleCorrida = False    #Elegir si se desea realizar una segunda corrida más detallada
paso1Corrida = 5       #Paso entre puntos de la primera corrida
paso2Corrida = 2        #Paso entre puntos de la segunda corrida
posicion = 100          #Posición de la muestra respecto a la lente
currI=0                 #Corriente a la que se desea volver antes de cambiar corriente (si se ha implementado esta función)
puntos=3               #Número de puntos que se toman para promediar y entregar una medida
tiempopos= 1

nombrearchivo = path+"\F-scan_%dmm_%s" % (posicion, dato)
print("Los archivos serán: "+nombrearchivo)

if os.path.exists(nombrearchivo+".txt") or os.path.exists(nombrearchivo+".png"):
    sys.exit("Error! : Los archivos ya existen")

def genNuevasPos(index, array):   #Genera nuevas corrientes a evaluar
    mean = (array.max()-array.min())/2.0 + array.min()
    print("Valor promedio :"+str(mean))
    threshold = mean
    pos = np.arange(len(index))[threshold>=array] #Encuentra las posiciones en el array en las que se añadirán más puntos
    print(pos)
    nuevasPos = np.array([])
    for i in pos: #Recordar que index[j] son posiciones que ya están en el array de corriente inicial!
        nuevasPos = np.append(nuevasPos, np.arange(index[i-1] + paso2Corrida, index[i], paso2Corrida))

    nuevasPos = np.append(index, nuevasPos)     #Se añaden nuevas posiciones a leer
    nuevasPos = nuevasPos[nuevasPos.argsort()]  #Se reordena el nuevo array
    return nuevasPos

def cambiarCorriente(x):  #Regresa a la posición "inicial" antes de buscar una nueva
    #o.current(currI)
    #time.sleep(0.5)     #Tiempo "pre" Previo
    o.current(x)
    time.sleep(tiempopos)     #Tiempo "pos" Posterior

#Iniciación comunicaciones seriales
o = Opto(port='COM4')
o.connect()

board = serial.Serial(port = 'COM3',baudrate = 9600,parity=serial.PARITY_NONE,stopbits=1,xonxoff=0,timeout=0.1)
board.write(b"W 0\r")
def leer():
    board.write(b"Q\r")
    lectura=board.readline()
    return float(lectura[:-4])


data = np.empty([0,2])
index = np.arange(0, 290 + 1, paso1Corrida)
#index = np.ones(20)*60
#index = np.arange(200, -1, -paso1Corrida)

print('Curr,    Rx')
cambiarCorriente(currI)

board.reset_input_buffer()  #Elimina valores que hayan en el buffer del Serial en el pc

plt.show()

# Se realiza una primera corrida de reconocimiento
try:
    for curr in index:  #Hasta 200 de a 5
            cambiarCorriente(curr)
            Rx = 0
            for xx in range(puntos):  #Promedio
                Rx = Rx + leer()
            Rx = Rx/puntos

            print(('%3.2f,  %3.2f')%(curr,Rx))

            data=np.append(data,[[curr,Rx]],axis=0)
            plt.cla()
            plt.plot(data[:,0],data[:,1],'ro-')
            plt.pause(0.1)

    #CORRIDA FINAL
    if dobleCorrida:
        new = genNuevasPos(index, data[:,1])
        print("Nuevos puntos a medir")
        print(new)
        data=np.empty([0,2]) #Se crea un data limpio para realizar una nueva la lectura.

        for curr in new:
                cambiarCorriente(curr)
                Rx = 0
                board.reset_input_buffer()
                for xx in range(puntos):  #Promedio
                    Rx = Rx + leer()
                Rx = Rx/puntos

                print(('%3.2f,  %3.2f')%(curr,Rx))
                data=np.append(data,[[curr,Rx]],axis=0)
                plt.cla()
                plt.plot(data[:,0],data[:,1],'ro-')
                plt.pause(0.1)

    #Guardado de datos
    np.savetxt(nombrearchivo +".txt", data, fmt='%.4f')
    plt.cla()
    plt.plot(data[:,0],data[:,1],'ro-')
    plt.title("F-scan %d mm" % posicion)
    plt.xlabel("Corriente [mA]")
    plt.ylabel("Voltaje Lock-in [mV]")
    plt.savefig(nombrearchivo +".png")
    print("Diferencia max-min: %f \n Diferencia relativa: %f"% (data[:,1].max()-data[:,1].min(), (data[:,1].max()-data[:,1].min())/data[:,1].max()))
    print("Desv Est %f" % data[:,1].std())
    #x = input() #Evita que al terminar el código, se cierre la gráfica

except KeyboardInterrupt:
    print('\nTERMINADO A PETICIÓN')

finally:
    o.close(soft_close=True)
    board.close()
    print("Programa finalizado")
