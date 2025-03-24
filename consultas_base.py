import MySQLdb.cursors
# import json


def un_dato(mysql, campos, tabla, condiciones, tipo):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SET lc_time_names = "es_ES"')
    tipo = tipo.lower()
    if tipo == "consulta":
        sql = 'select 1 from ' + tabla + " where " + condiciones
        print(sql)
        cursor.execute(sql)    
        datos = cursor.fetchone()
        cursor.close()
        if datos is None:
            return '0'
        else:
            return '1'
    return "X"

