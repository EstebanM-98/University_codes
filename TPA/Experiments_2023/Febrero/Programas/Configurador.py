# Crear ejecutable con pyinstaller.exe --onefile --windowed app.py
import PySimpleGUI as sg
import time
import serial
import numpy as np
from opto import Opto
import desplazadorL as dp
version = "0.8.6"

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

def main():
    layout = [[sg.Text("¿Qué dispositivo desea ajustar?", size=(50, 1))],
            [sg.Button("Corriente EFTL [mA]", key="-eftl-")],
            [sg.Button("Desplazador [mm]", key="-desp-")],
            [sg.Button("Disco [pasos]", key="-disco-")],
            [sg.Button("Lock-in Amplifier", key="-lockin-")],
            [sg.Text("Versión: %s"% version, size=(50, 1))],
            [sg.Button('Exit')]]

    window = sg.Window("Ajustar dispositivo", layout, layout, size=(400, 250))

    while True:
        event, values = window.read()
        if event == "Exit" or event == sg.WIN_CLOSED:
            break
        if event == "-eftl-":
            Eftl()
        if event == "-desp-":
            Desp()
        if event == "-disco-":
            Disco()
        if event == "-lockin-":
            lockin()

    window.close()

def leer(board):
    board.write(b"Q\r")
    lectura=board.readline()
    return float(lectura[:-4])

def modFase(board, grados=None):
    if grados == None:
        board.write(b"P\r")
        lectura=board.readline()
        return float(lectura[:-4])
    else:
        board.write(b"P %d\r" % grados)
        print(b"P %d\r" % grados)
        return 1000

def autoFase(board):
    gradosAct = modFase(board)
    print(gradosAct)
    iteraciones = 0

    # Ajuste grueso
    if leer(board)>0.5:
        while leer(board) > 0.0 and iteraciones<15:
            gradosAct += 15
            modFase(board, gradosAct)
            time.sleep(1)
            iteraciones +=1
    else:
        while leer(board) < 0.0 and iteraciones<15:
            gradosAct -= 15
            modFase(board, gradosAct)
            time.sleep(1)
            iteraciones +=1
        gradosAct += 15
        modFase(board, gradosAct)

    # Al llegar aquí el valor mostrado en el lock-in debe ser negativo
    # Como es un estado conocido, se ajustará cambiando de a un grado en una sola dirección, hasta fluctuar alrededor del cero.

    iteraciones = 0
    # Ajuste de precisión
    while abs(leer(board)) > 0.1 and iteraciones<10:
        if leer(board)>0.0:
            gradosAct += 1
            modFase(board, gradosAct)

        else :
            gradosAct -= 1
            modFase(board, gradosAct)
        time.sleep(1)
        iteraciones +=1

    modFase(board, gradosAct - 90)
    if leer(board) < -1:
        print("Corrigiendo signo")
        modFase(board, gradosAct - 180)

def lockin():
    layout = [[sg.Text("¿Ajustar phase?", size=(60, 1))],
            [sg.Txt(size=(30,1), key='-OUTPUT-')  ],
            [sg.Button("Ajustar", key="-ajustar-")],
            [sg.Button('Exit')]]
    window_lockin = sg.Window("Manejo de Lock-in", layout, size=(400, 200))
    try:
        board = serial.Serial(port = 'COM5',baudrate = 9600,parity=serial.PARITY_NONE,stopbits=1,xonxoff=0,timeout=0.1)
        board.write(b"W 0\r")
        while True:
            event, values = window_lockin.read()
            if event == "Exit" or event == sg.WIN_CLOSED:
                break
            if event == "-ajustar-":
                window_lockin['-OUTPUT-'].update("Ajustando fase")
                autoFase(board)
                window_lockin['-OUTPUT-'].update("Ajustada")
    except KeyboardInterrupt:
        board.close()
    finally:
        board.close()
        print("Fase Ajustada")

    window_lockin.close()

def Eftl():
    layout = [[sg.Text("¿A qué corriente desea ajustar la EFTL?", size=(60, 1))],
            [sg.Input(key="-corriente-")],
            [sg.Button("Ajustar", key="-ajustar-")],
            [sg.Button('Exit')]]

    window_Eftl = sg.Window("Ajustar EFTL", layout, size=(290, 200))
    
    o = Opto(port='COM3')
    o.connect()
    try:

        while True:
            event, values = window_Eftl.read()
            if event == "Exit" or event == sg.WIN_CLOSED:
                break
            if event == "-ajustar-":
                corriente = values["-corriente-"]
                
                o.current(int(corriente))
                print(corriente) #Accediendo al diccionario interno
                
    except KeyboardInterrupt:
        print("Programa terminado")
    finally:
        print("terminando programa")
        #o.close(soft_close=True)
        print("Ajuste EFRL finalizado")
    window_Eftl.close()

def Desp():
    layout = [[sg.Text("¿A qué distancia desea ajustar el Desplazador?, usar mm", size=(60, 1))],
            [sg.Input(key="-desplazamiento-")],
            [sg.Button("Ajustar", key="-ajustar-")],
            [sg.Button("Calibrar", key="-calib-")],
            [sg.Txt(size=(30,1), key='-Pactual-')  ],
            [sg.Txt(size=(30,1), key='-OUTPUT-')],
            [sg.Button('Exit')]]

    flagCalib = False

    window_Desp = sg.Window("Ajustar Desplazador", layout, size=(400, 250))

    try:
        pts=dp.detectar()
        print(pts)
        desp1,info1=dp.abrirpuertos("COM3")
        control_d = dp.desplazador(desp1)
        control_d.rapidez = 5*500

        mm_pos = None
        while True:
            event, values = window_Desp.read()
            if event == "Exit" or event == sg.WIN_CLOSED:
                break
            elif event == "-calib-":
                window_Desp['-OUTPUT-'].update("Calibrando")
                print("Calibrando")
                dp.cero(desp1)
                flagCalib = True
                mm_pos = 0
                window_Desp['-Pactual-'].update("Posición actual: %d mm" % mm_pos if mm_pos !=None else "Desconocida")
                window_Desp['-OUTPUT-'].update("Calibración Lista")
            elif event == "-ajustar-":
                try:
                    mm_pos = int(values["-desplazamiento-"])
                except ValueError:
                    window_Desp['-OUTPUT-'].update("Usar una posición valida")
                    continue

                if flagCalib:
                    window_Desp['-OUTPUT-'].update("Ajustando")
                    print("Ajustando")
                    print(mm_pos)
                    control_d.cambiar_pos(int(mm_pos*200))
                    window_Desp['-Pactual-'].update("Posición actual: %d mm" % mm_pos if mm_pos !=None else "Desconocida")
                    window_Desp['-OUTPUT-'].update("Ajuste Listo")
                else:
                    window_Desp['-OUTPUT-'].update("No se ha calibrado")

    except KeyboardInterrupt:
        desp1.close()
    finally:
        desp1.close()
        print("Ajuste desplazador finalizado")

    window_Desp.close()

def Disco():
    layout = [[sg.Text("¿En qué posición desea ajustar el Disco?", size=(50, 1))],
            [sg.Input(key="-rotacion-")],
            [sg.Button("Ajustar", key="-ajustar-")],
            [sg.Button("Calibrar", key="-calib-")],
            [sg.Txt(size=(30,1), key='-Pactual-')  ],
            [sg.Txt(size=(30,1), key='-OUTPUT-')  ],
            [sg.Button('Exit')]]

    window_Disco = sg.Window("Ajustar Disco", layout, size=(400, 250))

    try:
        serial_stepmotor = serial.Serial("COM6", 9600, timeout = 5.0)
        time.sleep(2) # Necesario para permitir inicializar al Arduino
        stepmotor = stepmotorclass(serial_stepmotor) #Instanciación del objeto que maneja el motor paso a paso

        posactual = None

        while True:
            event, values = window_Disco.read()
            if event == "Exit" or event == sg.WIN_CLOSED:
                break
            elif event == "-calib-":
                window_Disco['-OUTPUT-'].update("Calibrando")
                print("Calibrando")
                stepmotor.calibracion()
                posactual = 0
                window_Disco['-OUTPUT-'].update("Calibración Lista")
                window_Disco['-Pactual-'].update("Posición actual: %d " % posactual if posactual !=None else "Desconocida")
            elif event == "-ajustar-":
                grado = 0
                try:
                    grado = int(values["-rotacion-"])
                except ValueError:
                    window_Disco['-OUTPUT-'].update("Usar una posición valida")
                    continue

                window_Disco['-OUTPUT-'].update("Ajustando")
                window_Disco['-Pactual-'].update("Posición actual: %d " % posactual if posactual !=None else "Desconocida")
                print("Ajustando")
                posactual = grado
                print(grado)
                stepmotor.mover_a(grado)
                window_Disco['-OUTPUT-'].update("Ajuste Listo")
                window_Disco['-Pactual-'].update("Posición actual: %d " % posactual if posactual !=None else "Desconocida")

    except KeyboardInterrupt:
        serial_stepmotor.close()
    finally:
        serial_stepmotor.close()
        print("Ajuste disco finalizado")

    window_Disco.close()

if __name__ == "__main__":
    main()
