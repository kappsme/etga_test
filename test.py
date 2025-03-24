""" import json

x = json.dumps(
    {
        "saldo": 1,
        "monto_revision": 2,
        "monto_otros_cargos": 3,
        "monto_pagos": 4,
        "monto_cotizacion": 5,
    }
)
x = x + json.dumps({"carro": 1111,})
x = json.loads(x)
print(x) """

""" import mysql.connector """

""" # CONEXION A LA BASE DE DATOS
mydb = mysql.connector.connect(
    host="localhost", user="etga_usuario1_p", password="etga_usuario1xqi", database="etga_pruebas"
)

cursor = mydb.cursor()
cursor.execute("SET session time_zone = '-6:00'")
cursor.execute(
    "SELECT id_estado FROM boletas_estados be left join kapps_db.accounts a on be.id_usuario=a.id \
                WHERE be.id = (SELECT MAX(be2.id) FROM boletas_estados be2 \
                    WHERE be2.id_boleta = %s)",
    [157],
)

  # print(cursor.__dict__)
            # print(cursor._executed) # ULTIMO SQL EJECUTADO
#prueba=app_etga.root_path   # RUTA DE EJECUCION DEL APP
        
datos = cursor.fetchall()

print(datos)
 """


""" ENVIO DE CORREO SIN FLASK 

# CONFIGURACION DE CORREO ELECTRONICO
import smtplib
from email.message import EmailMessage
from socket import *


correo = smtplib.SMTP("mail.kapps.me", 587)
correo.login("electronicatorres@kapps.me", "etga$@28")

msg = EmailMessage()
msg['From'] =  "electronicatorres@kapps.me"
msg['To'] = "kenny_carcamo@hotmail.com"
try:
    msg.set_content("HOLA")
    msg['Subject'] = u"Mensaje de Electrónica Torres"
    correo.send_message(msg)
except (gaierror, ConnectionRefusedError):
# tell the script to report if your message was sent or which errors need to be fixed
    print('Failed to connect to the server. Bad connection settings?')
except smtplib.SMTPServerDisconnected:
    print('Failed to connect to the server. Wrong user/password?')
except smtplib.SMTPException as e:
    print('SMTP error occurred: ' + str(e))
else:
    print('OK')

"""


""" ENVIO DE CORREO SIN FLASK """

""" # CONFIGURACION DE CORREO ELECTRONICO
import smtplib
from email.message import EmailMessage
from socket import gaierror

print(1)
correo = smtplib.SMTP("smtpout.secureserver.net", 25)
print(2)
correo.login("servicioalcliente@electronicatorrescr.com", "Romanos12:21")
print(3)

msg = EmailMessage()
msg['From'] =  "servicioalcliente@electronicatorrescr.com"
msg['To'] = "kenny_carcamo@hotmail.com"
try:
    msg.set_content("HOLA")
    msg['Subject'] = u"Mensaje de Electrónica Torres"
    correo.send_message(msg)
except (gaierror, ConnectionRefusedError):
# tell the script to report if your message was sent or which errors need to be fixed
    print('Failed to connect to the server. Bad connection settings?')
except smtplib.SMTPServerDisconnected:
    print('Failed to connect to the server. Wrong user/password?')
except smtplib.SMTPException as e:
    print('SMTP error occurred: ' + str(e))
else:
    print('OK')
    
   ############################# JS leer una imgen en binario 
             if (registro["img1"] == "1") {
                    $.ajax({
                        url: '/imagenes/' + registro["id"] + "/1",
                        type: 'GET',
                        contentType: "image/jpg",
                        success: function (datos) {
                            // Render thumbnail.
                            var span = document.createElement('span');
                            span.innerHTML = ['<img class="thumb" src="', 'data:image/jpg;base64,' + datos, '"/>'].join('');
                            document.getElementById('list').insertBefore(span, null);
        
                            // document.getElementById('image').src = 'data:image/jpg;base64,' + result;
                        }
                    });
                }
    #Python
    with open(os.path.join(app_etga.root_path ,"inv_imagenes" , codigo + "_" + imagen + ".jpg"), "rb") as f:
        image_binary = f.read()
        response = make_response(base64.b64encode(image_binary))
        response.headers.set("Content-Type", "image/jpg")
        response.headers.set("Content-Disposition", "attachment", filename="image.jpg")
    return response
    
     """


## PRUEBA DE OS FILE READ IN SERVER

import os
import base64
from flask import Flask, Response, make_response

app_etga = Flask(__name__)
with open(os.path.join(app_etga.root_path, "inv_imagenes", "A00001_1.jpg"), "rb") as f:
    image_binary = f.read()
    response = make_response(base64.b64encode(image_binary))
    response.headers.set("Content-Type", "image/jpg")
    response.headers.set("Content-Disposition", "attachment", filename="image.jpg")