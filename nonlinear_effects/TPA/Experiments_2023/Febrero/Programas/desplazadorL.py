# -*- coding: utf-8 -*-
"""
Controlador para desplazador lineal
Autor: Dinntec SAS
Version: 1.0
Este controlador codifica por serial el modo, sentido, distancia
 y rapidez de desplazamiento

"""
import serial,time
from serial.tools import list_ports

#SE inicializan variables
desplazadores=[]  #lista de desplazadores encontrados
#estado_puertos=False #estado de revision de puertos
###

###Funciones
def un(modo):
    if modo=="mm":
        return ["mm","mm/s"]
    elif modo=="p":
        return ["pasos","pasos/s"]

def detectar():
    """
    Función que busca e identifica los puertos en los cuales está conectado algún desplazador lineal

    Devuelve
    -------
    puertos : Objeto tipo lista que contiene la ruta de los puertos que tienen algún desplazador lineal conectado

    """
    puertos=[i.device for i in list_ports.comports()]
    if len(puertos)==0:
        print("No hay desplazador conectado")
    elif len(puertos)==1:
        print("puerto localizado correctamente")
    elif len(puertos)>1:
        print("Hay ",len(puertos), "puertos activos")
    return puertos

def abrirpuertos(puerto_obj):
    """
    Función que configura el pueto seleccionado en el cual se encuentra conectado el desplazador lineal

    Parámetros
    ----------
    puerto_obj : objeto de tipo cadena (string), que contiene la ubicación del puerto serial en el cual está conectado el desplazador lineal.

    Returns
    -------
    ser : objeto de tipo serial que contiene la información del puerto en el cual está conectado el desplazador.
    desplazadores : objeto de tipo cadena (string), que contiene la información de identificación del desplazador actualmente activo

    """
    desplazadores=[]

    ser = serial.Serial(puerto_obj, 9600,timeout=2.0)
    time.sleep(2)
    ser.write(b'h')
    info = (ser.readline().decode('utf-8')).split(",")
    #print(info)
    print("modelo:",info[0], ", Firmware: ",info[1], ", url:", info[2][:18])
    if "DL" in info[0]:
        desplazadores.append([info[0],info[1][:3],info[2][:18]])
    else:
        ser.close()
    return ser,desplazadores

def mover(desp_obj,modo="mm",sentido=1, cantidad=1, rapidez=50):
    """
    Esta funcion envia la señal al desplazador activado:
    mover(...)
    mover(desp_obj,modo="mm",sentido=1, cantidad=1, rapidez=50)

    Parámetros
    ----------
    desp_obj: objeto de tipo serial que contiene la información del puerto en el cual está conectado el desplazador.
    modo: {'mm','p'} opcional, mm por defecto. Especifica el tipo de desplazamiento que se va a realizar, ya sea en milímetros (mm) o en pasos (p).
    sentido: entero {0,1}, opcional , 1 por defecto. Determina el sentido del desplazamiento 1 para ir al final 0 para ir al principio.
    cantidad: entero opcional, 1 por defecto. Indica la cantidad a desplazarse, se lee de acuerdo al modo seleccionado. Así si esta cantidad es 1 y el modo es 'mm', entonces el desplazamiento es de 1 mm; por otro lado si la cantidad es 1 y el modo es 'p', entonces el desplazamiento es de 1 paso.
    rapidez: entero opcional, 50 por defecto. especifica la rapidez del desplazamiento. Se lee de acuerdo al modo seleccionado. Así si el modo es 'mm' y la rapidez es 50 entonces  le desplazamiento se hace con una rapidez de 50 mm/s

    Devuelve
    ---------
    estado_desplazador: objeto tipo cadena (string) con el mensaje final "OK" indica que finalizó el desplazamiento correctamente, "FC1 OK" o "FC0 OK" indica que se detuvo por llegar a alguno de los extremos de desplazador.

    Ejemplos
    -------
    dp.mover(desp1,cantidad=10,sentido=0,rapidez=1)

    """
    desp_obj.write((modo+","+str(sentido)+","+str(cantidad)+","+str(rapidez)).encode())

    n=0
    u=un(modo)
    print("moviendo:",cantidad,u[0]," en sentido ",sentido, "con rapidez ", rapidez,u[1] )
    estado_desplazador= desp_obj.readline().decode('utf-8')
    while not("OK" in estado_desplazador):

        if n%100==0:
            print(".",end="")
        n=+1
        estado_desplazador= desp_obj.readline().decode('utf-8')

    print("")
    print(estado_desplazador)
    return estado_desplazador

def cero(desp_obj):
    """
    Función que lleva la plataforma del desplazador al inicio o cero del mismo

    Parámetros
    ----------
    desp_obj : Objeto tipo serial. Contiene la información del desplazador que está conectado actualmente.

    Devuelve
    -------
    Objeto tipo cadena con valor de 'OK'

    """
    desp_obj.write(b'0')
    n=0
    print("Ubicando el 0")
    while not("OK" in desp_obj.readline().decode('utf-8')):
        if n%100==0:
            print(".",end="")
        n=+1

    print("\n OK")
    return "OK"

class desplazador:
    def __init__(self, serial_object, tope=17):
        self.serial = serial_object
        self.tope = tope*10*200
        self.pos = 0
        self.rapidez = 5*200
        self.mode = "p" # "mm"

    def cero(self):
        cero(self.serial)
        self.pos = 0
    def cero_suave(self):
        self.cambiar_pos(0)
        mover(self.serial, modo=self.mode,cantidad=5,rapidez=100,sentido=0)
    def posicion(self):
        print("La posición actual es: "+str(self.pos))
    def cambiar_pos(self,new_pos):
        if new_pos <= self.tope:
            diferencia = new_pos - self.pos
            print("Se moverá a: "+str(new_pos)+" y se harán "+str(diferencia)+" pasos")
            if diferencia >= 0:
                mover(self.serial, modo=self.mode,cantidad=diferencia,rapidez=self.rapidez,sentido=1)
            else:
                mover(self.serial, modo=self.mode,cantidad=-diferencia,rapidez=self.rapidez,sentido=0)
            self.pos=self.pos+diferencia
        else:
            print("Sobrepasa la posición máxima debida!!")

####Principal
if __name__ == '__main__':
   print(detectar())
