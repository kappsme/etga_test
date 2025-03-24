# encoding: utf-8
import smtplib
from email.message import EmailMessage
import mysql.connector
from socket import *


""" class Correo:
    pass

correo =  Correo() 
correo.config = {}
correo.debug = False
correo.testing = False
correo.app_context() 
"""


# CONEXION A LA BASE DE DATOS
mydb = mysql.connector.connect(
  host="localhost",
  user="etga_usuario1",
  password="etga_usuario1xqi",
  database="etga"
)

# CONFIGURACION DE CORREO ELECTRONICO
correo = smtplib.SMTP("mail.kapps.me", 587)
correo.login("electronicatorres@kapps.me", "etga$@28")


# APLICACION ID = 2 ELECTRONICA TORRES
aplication_id = 2

# ENVIO CORREO
def envio_correo(tipo_mensaje, destinatario, adjunto, extra):
    msg = EmailMessage()
    msg['From'] =  "electronicatorres@kapps.me"
    # msg['To'] = "kenny_carcamo@hotmail.com"
    msg['To'] = destinatario
    if tipo_mensaje == 5:  # ENVIO DE NOTIFICACION DE RECHAZO
        try:
            msg.set_content(extra)
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
            return "OK"
    return 'E'


cursor=mydb.cursor()
cursor.execute("SET session time_zone = '-6:00'")
cursor.execute(
    "select a.id id_alerta, a.id_boleta \
        , acf.tipo, acf.mensaje, ec.correo  \
    from alertas a left join alertas_conf acf on acf.id=a.id_alerta_conf \
        left join boletas b on b.id_boleta=a.id_boleta \
        left join tx_clientes ec on ec.id=b.id_cliente \
    where a.estado=1 and acf.estado=1  \
        and acf.tipo = 'EMAIL' \
        and fecha_envio is null \
        and timestampdiff(day,a.fecha_ingreso,sysdate())>=dia"
)
datos = cursor.fetchall()
if datos is not None:
    tipo_mensaje = 5
    for alerta in datos:
        destinatario = alerta[4]
        mensaje = alerta[3]
        print(destinatario)
        resultado = envio_correo(tipo_mensaje, destinatario, "", mensaje)
        if resultado =='OK':
            print('Enviado')
            cursor.execute(
                "update alertas set fecha_envio=sysdate() where id=%s",[alerta[0]])



correo.quit()        
mydb.commit()
cursor.close()