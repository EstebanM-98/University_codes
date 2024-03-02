#Código sencillo que mueve el desplazador a una posición arbitraria, siempre ajustando primero a cero

import time
import serial
import numpy as np
import desplazadorL as dp
import matplotlib.pyplot as plt


#Iniciación comunicaciones seriales

pts=dp.detectar()
print(pts)

# Selecionar el puerto correspondiente al Desplazador
desp1,info1=dp.abrirpuertos("COM8")

#Inicializa el objeto desplazador con su correspondiente serial
control_d = dp.desplazador(desp1)
control_d.rapidez = 5*500
cm_pos = 12.7      #A Cuandos centimetros se moverá
# En el montaje actual para que la muestra esté a 10cm de la EFTL
# Mover 3.7 cm
# Para que esté en la focal de 0 mA mover a 12.7 cm

try:
    dp.cero(desp1)
    control_d.cambiar_pos(int(cm_pos*10*200))
    print("Se movió a %d" % int(cm_pos*10*200))

except KeyboardInterrupt:
    desp1.close()
    print("Programa terminado")

finally:
    desp1.close()
