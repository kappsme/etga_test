import MySQLdb.cursors

# import json


def datos_boleta(mysql, id_boleta):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SET lc_time_names = "es_ES"')
    cursor.execute(
        """SELECT id_boleta, date_format(fecha,"%%Y-%%b-%%d %%h:%%i%%p") fecha, id_cliente, m.nombre marca 
            , te.nombre tipo_equipo, motivo_cliente, comentario 
            , case id_condicion when 1 then "REGULAR" when 2 then "BUENA" when 3 then "DETERIORADO" end condicion 
            , boleta_tipo, boleta_garantia, serie, a1.username, modelo, ifnull(equipo_retirado,0) equipo_retirado, date_format(equipo_retirado_fecha,"%%Y-%%b-%%d %%h:%%i%%p") equipo_retirado_fecha, a2.username usuario_entrega 
            , ifnull(facturada,0) facturada, date_format(factura_fecha,"%%Y-%%b-%%d %%h:%%i%%p") factura_fecha, a3.username factura_usuario 
            , cerrada, a4.username cierre_usuario, date_format(cierre_fecha,"%%Y-%%b-%%d %%h:%%i%%p") cierre_fecha, cierre_comentario, cierre_anticipado, sin_pagos, boleta_tipo, boleta_garantia, boleta_original 
            , ifnull(timestampdiff(day,equipo_retirado_fecha,sysdate()),0) dias_cerrada 
            , ifnull(dias_habiles,0) dias_habiles, rechazada, dias_garantia 
            FROM boletas left join kapps_db.accounts a1 on a1.id=id_usuario 
                left join kapps_db.accounts a2 on a2.id=equipo_retirado_id_usuario 
                left join kapps_db.accounts a3 on a3.id=factura_id_usuario 
                left join kapps_db.accounts a4 on a4.id=cierre_id_usuario 
                left join marcas m on m.id=id_marca 
                left join tipos_equipo te on te.id=id_tipo_equipo 
                WHERE id_boleta = %s""",
        [id_boleta],
    )
    datos = cursor.fetchone()
    cursor.close()
    return datos


def datos_boleta_impresion(mysql, id_boleta):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SET lc_time_names = "es_ES"')
    cursor.execute(
        'SELECT id_boleta, date_format(fecha,"%%Y-%%b-%%d %%h:%%i%%p") fecha, id_cliente, m.nombre marca \
            , te.nombre tipo_equipo, motivo_cliente, comentario \
            , boleta_tipo, boleta_garantia , modelo, serie, username, nombres, apellidos, n_documento \
            , case id_condicion when 1 then "REGULAR" when 2 then "BUENA" when 3 then "DETERIORADO" end condicion \
            , case tipo_documento when 1 then "CEDULA" when 2 then "RESIDENCIA" when 3 then "PASAPORTE" when 4 then "CEDULA JURIDICA" else "OTRO" end tipo_documento \
            , telefono, correo, tipo_cliente, boleta_tipo, boleta_garantia, boleta_original, dias_habiles \
            FROM boletas left join kapps_db.accounts on id_usuario=id \
                left join marcas m on m.id=id_marca \
                left join tipos_equipo te on te.id=id_tipo_equipo \
                left join tx_clientes cl on cl.id=boletas.id_cliente \
                WHERE id_boleta = %s',
        [id_boleta],
    )
    datos = cursor.fetchone()
    cursor.close()
    return datos


def datos_movimientos(mysql, id_boleta, id_estado, cierre_anticipado):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SET lc_time_names = "es_ES"')
    sql = (
        'select id, date_format(fecha,"%Y-%b-%d %h:%i%p") fecha, monto, tipo, medio, concepto, username, estado, username_anula, fecha_anula, impuesto, fecha fechax from ( \
        select mov.id,  fecha, monto, tipo \
                    , case when medio=0 then "" when medio=1 then "Efectivo" when medio=2 then "Tarjeta Cred/Deb" when medio=3 then "Transferencia" end medio \
                    , concepto, t2.username, mov.estado, t3.username username_anula, fecha_anula, impuesto \
                    from movimientos mov left join kapps_db.accounts t2 on t2.id = mov.id_usuario \
                        left join kapps_db.accounts t3 on t3.id = mov.id_usuario_anula \
                    WHERE id_boleta = '
        + str(id_boleta)
    )
    # SI HAY COTIZACION
    if id_estado >= 4 and id_estado != 7 and cierre_anticipado == 0:
        sql += (
            ' union all \
            select b.id, fecha, monto, 6, 4 ,"Costo Reparación", t4.username, 1,"","","" from boletas_cotizaciones b \
            left join kapps_db.accounts t4 on t4.id = b.id_usuario \
                where id_boleta='
            + str(id_boleta)
            + " and b.estado=1"
        )
    # SI TIENE DESCUENTOS Y YA ESTA EN FACTURACION
    if id_estado >= 6:
        sql += (
            ' union all \
            select d.id, fecha_creacion, monto*(1+ifnull(contenido,1)/100),7,"", td.descriptor, t5.username,d.estado, t6.username,d.fecha_anula,"" \
            from boletas_descuentos d \
            left join kapps_db.accounts t5 on t5.id = d.id_usuario \
            left join kapps_db.accounts t6 on t6.id = d.id_usuario_anula \
            left join tipos_descuento td on td.id= d.id_tipo_descuento \
            left join datos dd on dd.id=(case when d.id_tipo_descuento=1 then 15 when d.id_tipo_descuento=2 then 15 when d.id_tipo_descuento=3 then 15 when d.id_tipo_descuento=4 then 8 end) \
                where id_boleta='
            + str(id_boleta)
        )
    
    sql +=") tab order by fechax asc"

    # BODEGAJE
    # SI EXISTE COMPROBANTE

    # SI NO EXISTE COMPROBANTE
    cursor.execute(sql)
    datos = cursor.fetchall()
    cursor.close()
    return datos


def datos_movimiento_unico(mysql, id_movimiento):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SET lc_time_names = "es_ES"')
    cursor.execute(
        'select mov.id, date_format(mov.fecha,"%%Y-%%b-%%d %%h:%%i%%p") fecha, monto, tipo \
                    , case when medio=0 then "" when medio=1 then "Efectivo" when medio=2 then "Tarjeta Cred/Deb" end medio, concepto, t2.username, mov.estado \
                    , nombres, apellidos \
                    from movimientos mov left join kapps_db.accounts t2 on t2.id = mov.id_usuario \
                    left join boletas b on b.id_boleta=mov.id_boleta \
                    left join tx_clientes cl on cl.id=b.id_cliente \
                    WHERE mov.id = %s',
        [id_movimiento],
    )
    datos = cursor.fetchone()
    cursor.close()
    return datos


def datos_estado(mysql, id_boleta):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SET lc_time_names = "es_ES"')
    id_boleta = int(id_boleta)
    cursor.execute(
            """select (select contenido from datos where id=3) rechazo, 
            (select contenido from datos where id=4) sin_retiro 
            from dual"""
    )
    datos_dias = cursor.fetchone()
    dias_bodegaje_sin_retiro = int(datos_dias["sin_retiro"])
    sql="""SELECT id_estado, date_format(be.fecha,'%Y-%b-%d %h:%i%p') fecha, username,
                case when be.id_estado=6 and b.equipo_retirado = 0 and timestampdiff(day,be.fecha,sysdate())>={0} then 1 
				    when be.id_estado=7 and b.equipo_retirado = 0 and timestampdiff(day,be.fecha,sysdate())>={0} then 1 
                else 0 end bodegaje 
            FROM boletas_estados be left join kapps_db.accounts a on be.id_usuario=a.id
            left join boletas b on b.id_boleta=be.id_boleta
                WHERE be.id = (SELECT MAX(be2.id) FROM boletas_estados be2 
                    WHERE be2.id_boleta = {1})""".format(dias_bodegaje_sin_retiro,id_boleta)
    print(sql)
    cursor.execute(sql)
    datos = cursor.fetchone()
    cursor.close()
    return datos


def datos_cliente(mysql, id_boleta):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SET lc_time_names = "es_ES"')
    id_boleta = int(id_boleta)
    cursor.execute("SELECT id_cliente FROM boletas WHERE id_boleta = %s", [id_boleta])
    datos = cursor.fetchone()
    id_cliente = datos["id_cliente"]
    cursor.execute(
        "SELECT c.*, z.nombre zona FROM tx_clientes c  \
        left join zonas z on z.id=c.id_zona WHERE c.id = %s",
        [id_cliente],
    )
    datos = cursor.fetchone()
    cursor.close()
    return datos


def datos_reportes(mysql, id_reporte, fecha_inicio, fecha_fin, tipo_accion2=0):
    datos = [0, 0, 0]
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SET lc_time_names = "es_ES"')
    filtro=''
    if id_reporte == 1:  # PAGOS y ANULACIONES (tipo 1 taller , tipo 10 Tienda)
        filtro='1,10'
        if tipo_accion2==1:
            filtro='1'
        if tipo_accion2==2:
            filtro='10'
        
        sql = (
            'select * from (select m.id, date_format(fecha,"%Y-%b-%d %h:%i%p") fecha ,case when medio=0 then "" when medio=1 then "Efectivo" when medio=2 then "Tarjeta Cred-Deb" when medio=3 then "Transferencia" end medio \
                , monto, a.username, case when tipo=1 then id_boleta when tipo=10 then id_venta end id_boleta, m.estado, ifnull(a2.username,"") usuario_anula, ifnull(date_format(m.fecha_anula,"%Y-%b-%d %h:%i%p"),"") fecha_anula, \
                case when tipo=1 then "Taller" when tipo=10 then "Tienda" end origen, fecha fechax \
            from movimientos m left join kapps_db.accounts a on a.id=m.id_usuario \
                left join kapps_db.accounts a2 on a2.id=m.id_usuario_anula \
            where (fecha between date("'
            + fecha_inicio
            + '") and date_add("'
            + fecha_fin
            + '", INTERVAL 1 DAY ) \
                or fecha_anula between date("'
            + fecha_inicio
            + '") and date_add("'
            + fecha_fin
            + '", INTERVAL 1 DAY )) \
                and tipo in ('+ filtro + ')'
        )
        if tipo_accion2 != 1:
            sql= sql + ' union all \
                select ll3.id, date_format(ll3.fecha,"%Y-%b-%d %h:%i%p") fecha , "Devolución", monto_sin_impuestos+impuestos, username, parametro, 2 estado,"" usuario_anula,"" fecha_anula, "Tienda", fecha fechax \
                from inv_lotes_log ll3 left join kapps_db.accounts a on a.id=ll3.id_usuario \
            where fecha between date("' + fecha_inicio + '") and date_add("'+ fecha_fin+ '", INTERVAL 1 DAY ) \
                and tipo=5) t order by fechax asc'
        else:
            sql= sql + ') t order by fechax asc'
        cursor.execute(sql)
        resultado = cursor.fetchall()
        campos = [i[0] for i in cursor.description]
        total_efectivo = 0
        conteo_efectivo = 0
        total_tarjetas = 0
        conteo_tarjetas = 0
        total_transferencias = 0
        conteo_transferencias = 0
        total_anulaciones = 0
        conteo_anulaciones = 0
        tienda_total_efectivo = 0
        tienda_conteo_efectivo = 0
        tienda_total_tarjetas = 0
        tienda_conteo_tarjetas = 0
        tienda_total_transferencias = 0
        tienda_conteo_transferencias = 0
        tienda_total_anulaciones = 0
        tienda_conteo_anulaciones = 0
        # DETALLE
        if resultado is not None:
            datos[2] = resultado
            # TOTALES 
            for row in resultado:
                # TALLER
                if row["medio"] == "Efectivo" and row["origen"]=="Taller" and row["estado"] == 1:
                    total_efectivo += float(row["monto"])
                    conteo_efectivo += 1
                if row["medio"] == "Tarjeta Cred-Deb" and row["origen"]=="Taller" and row["estado"] == 1:
                    total_tarjetas += float(row["monto"])
                    conteo_tarjetas += 1
                if row["medio"] == "Transferencia" and row["origen"]=="Taller" and row["estado"] == 1:
                    total_transferencias += float(row["monto"])
                    conteo_transferencias += 1
                if row["estado"] == 0 and row["origen"]=="Taller":
                    total_anulaciones += float(row["monto"])
                    conteo_anulaciones += 1
                # TIENDA
                if row["medio"] == "Efectivo" and row["origen"]=="Tienda" and row["estado"] == 1:
                    tienda_total_efectivo += float(row["monto"])
                    tienda_conteo_efectivo += 1
                if row["medio"] == "Tarjeta Cred-Deb" and row["origen"]=="Tienda" and row["estado"] == 1:
                    tienda_total_tarjetas += float(row["monto"])
                    tienda_conteo_tarjetas += 1
                if row["medio"] == "Transferencia" and row["origen"]=="Tienda" and row["estado"] == 1:
                    tienda_total_transferencias += float(row["monto"])
                    tienda_conteo_transferencias += 1
                if row["estado"] == 2 and row["origen"]=="Tienda":
                    tienda_total_anulaciones += float(row["monto"])
                    tienda_conteo_anulaciones += 1
        datos[0] = [
            total_efectivo,
            conteo_efectivo,
            total_tarjetas,
            conteo_tarjetas,
            total_transferencias,
            conteo_transferencias,
            total_anulaciones,
            conteo_anulaciones,
        ]
        datos[1] = [
            tienda_total_efectivo,
            tienda_conteo_efectivo,
            tienda_total_tarjetas,
            tienda_conteo_tarjetas,
            tienda_total_transferencias,
            tienda_conteo_transferencias,
            tienda_total_anulaciones,
            tienda_conteo_anulaciones,
        ]
    if id_reporte == 3:  # FACTURACION
        sql = (
            'select date_format(fecha_ingreso,"%Y-%b-%d %h:%i%p") fecha_ingreso, id_comprobante comprobante \
                , sum(monto) monto, sum(impuestos) impuestos, estado, id_boleta, factura \
            from boletas_facturas \
            where fecha_ingreso between date("'
            + fecha_inicio
            + '") and date_add("'
            + fecha_fin
            + '", INTERVAL 1 DAY ) \
            group by date_format(fecha_ingreso,"%Y-%b-%d %h:%i%p"), id_comprobante, estado, id_boleta, factura'
        )
        cursor.execute(sql)
        resultado = cursor.fetchall()
        campos = [i[0] for i in cursor.description]
        total_monto = 0
        total_impuestos = 0
        conteo = 0
        # DETALLE
        if resultado is not None:
            datos[1] = resultado
            # TOTALES
            for row in resultado:
                if row["estado"] == 1:
                    total_monto += float(row["monto"])
                    total_impuestos += float(row["impuestos"])
                    conteo += 1
        datos[0] = [total_monto, total_impuestos, conteo]
    if id_reporte == 4:  # DETALLE BOLETAS
        sql = (
            'select b.id_boleta boleta, date_format(b.fecha,"%Y-%b-%d %h:%i%p") fecha_ingreso, case when boleta_original = 0 then "Normal" else "Garantía" end tipo_boleta \
            , if(boleta_original=0,"",boleta_original) boleta_original, te.nombre tipo_equipo, m.nombre marca \
            , date_format(bd.fecha,"%Y-%b-%d %h:%i%p") fecha_diagnostico, acd.username usuario_diagnostico, 0 horas_diagnostico \
            , date_format(bcot.fecha,"%Y-%b-%d %h:%i%p") fecha_cotizacion, accot.username usuario_cotizacion, 0 horas_cotizacion \
            , date_format(be_er.fecha,"%Y-%b-%d %h:%i%p") fecha_entra_reparacion , date_format(ber.fecha,"%Y-%b-%d %h:%i%p") fecha_sale_reparacion \
            , acr.username usuario_reparacion, round(ber.tiempo/60,2) horas_reparacion \
            , (select ifnull(sum(costo*cantidad),0) from boletas_repuestos rr where rr.id_boleta=b.id_boleta and rr.estado=1) costo_repuestos \
            , (select ifnull(round(sum(monto),2),0) from boletas_facturas fac where fac.id_boleta=b.id_boleta and fac.estado=1 and concepto in ("Repuestos Nuevos","Repuestos Usados")) factura_repuestos_NII \
            , ifnull(bcomp.monto,0) facturado_NII, ifnull(bcomp.impuestos,0) impuestos \
            , case when cerrada=1 then "Cerrada" else "Abierta" end estado \
            , date_format(b.cierre_fecha,"%Y-%b-%d %h:%i%p") cierre_fecha \
            , case when cierre_anticipado=1 then "SI" else "NO" end cierre_anticipado \
            , date_format(b.equipo_retirado_fecha,"%Y-%b-%d %h:%i%p") equipo_retiro_fecha \
            , date_format(b.factura_fecha,"%Y-%b-%d %h:%i%p") factura_fecha \
            , b.motivo_cliente, bd.descripcion motivo_reparado, b.cierre_comentario \
            from boletas b \
            left join tipos_equipo te on te.id=b.id_tipo_equipo  \
            left join marcas m on m.id=b.id_marca \
            left join boletas_estados be_er on be_er.id_boleta=b.id_boleta \
                and be_er.id_estado=4 \
                and be_er.id=(select max(id) from boletas_estados be3 where be3.id_boleta=b.id_boleta and be3.id_estado=4) \
                left join kapps_db.accounts acrd on acrd.id=be_er.id_usuario \
            left join boletas_estados ber on ber.id_boleta=b.id_boleta \
                and ber.id_estado=5 \
                and ber.id=(select max(id) from boletas_estados be2 where be2.id_boleta=b.id_boleta and be2.id_estado=5) \
                left join kapps_db.accounts acr on acr.id=ber.id_usuario \
            left join boletas_diagnosticos bd on bd.id_boleta=b.id_boleta \
                left join kapps_db.accounts acd on acd.id=bd.id_usuario \
            left join boletas_cotizaciones bcot on bcot.id_boleta=b.id_boleta and bcot.estado=1 \
                left join kapps_db.accounts accot on accot.id=bcot.id_usuario \
                left join boletas_comprobantes bcomp on bcomp.id_boleta=b.id_boleta and facturado=1 \
            where b.fecha between date("'
            + fecha_inicio
            + '") and date_add("'
            + fecha_fin
            + '", INTERVAL 1 DAY )'
        )
        cursor.execute(sql)
        resultado = cursor.fetchall()
        campos = [i[0] for i in cursor.description]
        if resultado is not None:
            datos[1] = resultado
    if id_reporte == 5:  # TIEMPOS
        sql = ( 
            'select * from ( select date_format(bd.fecha,"%Y-%m-%d") fecha, "Diagnóstico" tipo, a.username, concat(truncate(tiempo/60,0),"h ",tiempo-truncate(tiempo/60,0)*60,"m") tiempo, id_boleta \
            from boletas_diagnosticos bd left join kapps_db.accounts a on a.id=bd.id_usuario \
            WHERE bd.fecha between date("'
            + fecha_inicio
            + '") and date_add("'
            + fecha_fin
            + '", INTERVAL 1 DAY ) '
            + 'union all \
            select date_format(be.fecha,"%Y-%m-%d") fecha, "Reparación" tipo, a2.username, concat(truncate(tiempo/60,0),"h ",tiempo-truncate(tiempo/60,0)*60,"m") tiempo, id_boleta \
            from boletas_estados be left join kapps_db.accounts a2 on a2.id=be.id_usuario \
            where be.fecha between date("'
            + fecha_inicio
            + '") and date_add("'
            + fecha_fin
            + '", INTERVAL 1 DAY ) and id_estado=5) t order by fecha desc')
        cursor.execute(sql)
        resultado = cursor.fetchall()
        campos = [i[0] for i in cursor.description]
        if resultado is not None:
            datos[1] = resultado
    if id_reporte == 6:  # VENTAS
        filtro='"TIENDA","TALLER"'
        if tipo_accion2==1:
            filtro='"TALLER"'
        if tipo_accion2==2:
            filtro='"TIENDA"'
        sql = ('select llc.origen, llc.nombre tipo,  date_format(ll.fecha,"%Y-%b-%d %h:%i%p") fecha, parametro, p.id codigo , p.nombre producto, m.nombre marca, \
                p.modelo, pe.descripcion condicion , ll.unidades, ifnull(monto_sin_impuestos,0) monto_sin_impuestos, ifnull(impuestos,0) impuestos, ifnull(l.costo_unitario,0)*ll.unidades costo, a.username usuario \
            from inv_lotes_log ll \
                left join inv_lotes_log_cat llc on ll.tipo=llc.id \
                left join inv_lotes l on l.id=ll.id_lote \
                left join inv_productos p on p.id=l.codigo_producto \
                left join inv_productos_estados pe on pe.id=p.estado \
                left join marcas m on m.id=p.id_marca \
                left join kapps_db.accounts a on a.id=ll.id_usuario \
            where ll.tipo in (2,3,4,5) and llc.origen in ('+ filtro +') \
                and  ll.fecha between date("'
                + fecha_inicio
                + '") and date_add("'
                + fecha_fin
                + '", INTERVAL 1 DAY ) order by ll.fecha asc')
        cursor.execute(sql)
        resultado = cursor.fetchall()
        campos = [i[0] for i in cursor.description]
        total_productos = 0
        total_anulaciones = 0
        total_monto_sin_impuestos = 0
        total_impuestos = 0
        total_costo = 0
        tienda_total_productos = 0
        tienda_total_anulaciones = 0
        tienda_total_monto_sin_impuestos = 0
        tienda_total_impuestos = 0
        tienda_total_costo = 0
        # DETALLE
        if resultado is not None:
            datos[2] = resultado
            # TOTALES 
            for row in resultado:
                # TALLER
                if row["origen"] == "TALLER":
                    if row["tipo"]=="ANULACION DE REPUESTO EN BOLETA":
                        total_monto_sin_impuestos -= float(row["monto_sin_impuestos"])
                        total_impuestos -= float(row["impuestos"])
                        total_costo -= float(row["costo"])
                        total_anulaciones += float(row["unidades"])
                    else:
                        total_monto_sin_impuestos += float(row["monto_sin_impuestos"])
                        total_impuestos += float(row["impuestos"])
                        total_costo += float(row["costo"])
                        total_productos += float(row["unidades"])
                # TIENDA
                if row["origen"] == "TIENDA":
                    if row["tipo"]=="ANULACION DE VENTA" or row["tipo"]=="DEVOLUCION":
                        tienda_total_monto_sin_impuestos -= float(row["monto_sin_impuestos"])
                        tienda_total_impuestos -= float(row["impuestos"])
                        tienda_total_costo -= float(row["costo"])
                        tienda_total_anulaciones += float(row["unidades"])
                    else:
                        tienda_total_monto_sin_impuestos += float(row["monto_sin_impuestos"])
                        tienda_total_impuestos += float(row["impuestos"])
                        tienda_total_costo += float(row["costo"])
                        tienda_total_productos += float(row["unidades"])
        datos[0] = [
            total_monto_sin_impuestos,
            total_impuestos,
            total_costo,
            total_productos,
            total_anulaciones,
        ]
        datos[1] = [
            tienda_total_monto_sin_impuestos,
            tienda_total_impuestos,
            tienda_total_costo,
            tienda_total_productos,
            tienda_total_anulaciones,
        ]
    if id_reporte == 7:  # INVENTARIO - EXISTENCIAS
        sql = ( 
            'select l.id "id lote", date_format( l.fecha_ingreso,"%Y-%b-%d %h:%i%p") "fecha ingreso", l.codigo_producto , p.nombre "Producto", p.modelo Modelo, m.nombre Marca, a.username usuario \
                ,l.unidades, l.disponibilidad, l.ubicacion, precio_venta precio_unitario_venta, precio_taller precio_unitario_taller, costo_unitario \
            from inv_lotes l left join inv_productos p on l.codigo_producto = p.id \
                left join marcas m on m.id=p.id_marca \
                left join kapps_db.accounts a on a.id=l.id_usuario_ingresa \
            where disponibilidad>0')
        cursor.execute(sql)
        resultado = cursor.fetchall()
        campos = [i[0] for i in cursor.description]
        if resultado is not None:
            datos[0] = resultado
            datos[1] = {
                "lotes": cursor.rowcount,   
                "productos": len(set([row["codigo_producto"] for row in resultado])),
                "unidades": sum([row["disponibilidad"] for row in resultado]),   
            }
    if id_reporte == 9:  # DETALLE LIQUIDACION
        sql = ('select liquidacion "fecha liquidacion", a1.username "usuario liquidacion" \
                    , l.costo_unitario "costo unitario taller", br.costo "costo unitario tienda", br.costo_factura "precio unitario factura", br.cantidad unidades \
                    , ifnull(l.costo_unitario*cantidad,0) "costo total taller", br.costo*cantidad "costo total tienda", br.costo_factura*cantidad "precio total factura" \
                    ,a2.username "usuario reparacion" ,br.id_boleta boleta, concat(p.id, " - ", p.nombre," ", p.modelo) repuesto \
                from boletas_repuestos br \
                    left join kapps_db.accounts a1 on br.liquidacion_usuario = a1.id \
                    left join kapps_db.accounts a2 on br.id_usuario = a2.id \
                    left join inv_productos p on p.id = br.info \
                    left join inv_lotes_log ll on ll.comentario=br.id \
                    left join inv_lotes l on ll.id_lote=l.id \
                where br.liquidacion is not null and br.estado=1 \
                    and  br.liquidacion between date("'
                + fecha_inicio
                + '") and date_add("'
                + fecha_fin
                + '", INTERVAL 1 DAY ) order by br.liquidacion asc')                    
        cursor.execute(sql)
        resultado = cursor.fetchall()
        campos = [i[0] for i in cursor.description]
        if resultado is not None:
            datos[0] = resultado
            datos[1] = {
                "costo taller": sum([row["costo total taller"] for row in resultado]),  
                "costo tienda": sum([row["costo total tienda"] for row in resultado]),  
                "precio factura": sum([row["precio total factura"] for row in resultado]),  
                "repuestos": sum([row["unidades"] for row in resultado]),
                "liquidaciones": len(set([row["fecha liquidacion"] for row in resultado])),    
            }
    cursor.close()
    return datos, campos, sql, filtro


def datos_historial(mysql, id_boleta, tipo_accion):
    cursor = mysql.connection.cursor()
    if tipo_accion == 1:  # HISTORIAL COMPLETO
        sql = (
            'select date_format(fecha,"%Y-%b-%d %h:%i:%S %p"), accion, comentario, usuario \
            from (select t.fecha fecha, \
                case when tipo in (2,5) then "CARGO"  \
                when tipo=1 then "PAGO" \
                else "NO DEFINIDO" \
            end accion, concat(case when t.medio=1 then "[Efectivo]" when t.medio=2 then "[Tarjeta]" when t.medio=3 then "[Transferencia]" when t.medio=0 then "" else "[N/A]" end," ₡",FORMAT(monto,"Currency")," por ", t.concepto) comentario, a.username usuario\
            from movimientos t left join kapps_db.accounts a on a.id=t.id_usuario  \
            where t.id_boleta='
            + id_boleta
            + ' \
            union all \
            select t.fecha_anula,  \
            case when tipo in (2,5) then "Cargo Anulado"  \
                when tipo=1 then "Pago Anulado" \
                else "NO DEFINIDO" \
            end accion, concat("₡",FORMAT(monto,"Currency")," por ", t.concepto) comentario, a.username \
            from movimientos t left join kapps_db.accounts a on a.id=t.id_usuario_anula  \
            where t.id_boleta='
            + id_boleta
            + ' and t.estado=0 \
            union all \
            select t.fecha, "Ingreso de Diagnóstico" accion, "" comentario, a.username  \
            from boletas_diagnosticos t left join kapps_db.accounts a on a.id=t.id_usuario \
            where t.id_boleta='
            + id_boleta
            + ' \
            union all \
            select t.fecha, case when tipo=1 then "Comentario" when tipo=2 then "Modificación a Diagnóstico" when tipo=3 then "Cotización enviada por Correo" \
                when tipo=4 then "Motivo Rechazo" else "N/A" end accion \
                , t.comentario, a.username  \
            from boletas_comentarios t left join kapps_db.accounts a on a.id=t.id_usuario \
            where t.id_boleta='
            + id_boleta
            + ' \
            union all \
            select t.fecha, "Cotización" accion,  concat("Por ₡",FORMAT(monto,"Currency")) comentario, a.username  \
            from boletas_cotizaciones t left join kapps_db.accounts a on a.id=t.id_usuario \
            where t.id_boleta='
            + id_boleta
            + ' \
            union all \
            select t.fecha_cambia_estado, " Anulación de Cotización" accion, concat("Por ₡",FORMAT(monto,"Currency")) comentario, a.username  \
            from boletas_cotizaciones t left join kapps_db.accounts a on a.id=t.id_usuario_cambia_estado \
            where t.id_boleta='
            + id_boleta
            + ' and t.estado=0 \
            union all \
            select t.fecha, "Agrega Repuesto" accion, rep.nombre, a.username  \
            from boletas_repuestos t left join repuestos rep on t.id_repuesto=rep.id \
            left join kapps_db.accounts a on a.id=t.id_usuario \
            where id_boleta='
            + id_boleta
            + ' \
            union all \
            select t.fecha_modifica,"Anula Repuesto" accion, rep.nombre, a.username  \
            from boletas_repuestos t left join repuestos rep on t.id_repuesto=rep.id \
            left join kapps_db.accounts a on a.id=t.id_usuario_modifica \
            where id_boleta='
            + id_boleta
            + ' and t.estado=0 \
            union all \
            select t.fecha, "Crea Comprobante" accion, concat("TOTAL ₡",FORMAT(monto+impuestos,"Currency") \
            ," [Monto ₡",FORMAT(monto,"Currency")," + Impuestos ₡",FORMAT(impuestos,"Currency"),"] [", \
            "Tipo Cliente: ", case when tipo_cliente=1 then "Natural" when tipo_cliente=1 then "Natural" when tipo_cliente=1 then "Natural" else "N/A" end,"]") comentario, a.username \
            from boletas_comprobantes t \
            left join kapps_db.accounts a on a.id=t.id_usuario \
            where t.id_boleta='
            + id_boleta
            + ' \
            union all \
            select t.fecha_anula, "Anula Comprobante" accion, concat("TOTAL ₡",FORMAT(monto+impuestos,"Currency") \
            ," [Monto ₡",FORMAT(monto,"Currency")," + Impuestos ₡",FORMAT(impuestos,"Currency"),"] [", \
            "Tipo Cliente: ", case when tipo_cliente=1 then "Natural" when tipo_cliente=1 then "Natural" when tipo_cliente=1 then "Natural" else "N/A" end,"]") comentario, a.username \
            from boletas_comprobantes t \
            left join kapps_db.accounts a on a.id=t.id_usuario_anula \
            where t.id_boleta='
            + id_boleta
            + ' and t.estado=0 \
            union all \
            select equipo_retirado_fecha, "Equipo Entregado A Cliente", "" comentario,  a.username \
            from boletas b left join kapps_db.accounts a on a.id=b.equipo_retirado_id_usuario \
            where id_boleta='
            + id_boleta
            + ' and b.equipo_retirado=1 \
            union all \
            select factura_fecha, "Ingreso de Factura", "" comentario,  a.username \
            from boletas b left join kapps_db.accounts a on a.id=b.factura_id_usuario \
            where id_boleta='
            + id_boleta
            + ' and b.facturada=1 \
            union all \
            select cierre_fecha, "Cierre Anticipado", concat("Motivo: ",cierre_comentario) comentario, a.username \
            from boletas b left join kapps_db.accounts a on a.id=b.cierre_id_usuario \
            where b.id_boleta='
            + id_boleta
            + ' and b.cierre_anticipado=1 \
            union all \
            select t.fecha, concat("Cambio a ",  \
                case when id_estado=0 then "NUEVA" \
                when id_estado=1 then "DIAGNOSTICO" \
                when id_estado=2 then "COTIZACION" \
                when id_estado=3 then "ESPERA DE CONFIRMACION DE CLIENTE" \
                when id_estado=4 then "REPARACION" \
                when id_estado=5 then "LISTA PARA RETIRO" \
                when id_estado=6 then "FACTURACION" \
                when id_estado=7 then "RECHAZO" \
                when id_estado=10 then "CIERRE" \
                else "NO DEFINIDO" \
                end ), "", a.username \
                from boletas_estados t left join kapps_db.accounts a on a.id=t.id_usuario  \
            where t.id_boleta='
            + id_boleta
            + ") t2 order by t2.fecha asc"
        )
    if tipo_accion == 2:  # HISTORIAL DE COMENTARIOS
        sql = (
            "select date_format(fecha,'%Y-%b-%d %h:%i:%S %p'), t.comentario, a.username  \
            from boletas_comentarios t left join kapps_db.accounts a on a.id=t.id_usuario \
            where t.id_boleta="
            + id_boleta
            + " and t.tipo=1"
        )
    cursor.execute(sql)
    resultado = cursor.fetchall()
    cursor.close()
    return resultado


def datos_saldo(mysql, id_boleta):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SET lc_time_names = "es_ES"')
    # EXTRAE EL TIPO DE CLIENTE Y SI TIENE CIERRE ANTICIPADO
    cursor.execute(
        "SELECT cierre_anticipado, tipo_cliente, rechazada \
        FROM boletas b left join tx_clientes ec on ec.id=b.id_cliente WHERE id_boleta = %s",
        [id_boleta],
    )
    datos = cursor.fetchone()
    cierre_anticipado = datos["cierre_anticipado"]
    tipo_cliente = datos["tipo_cliente"]
    rechazada = int(datos["rechazada"])
    # ESTADO ACTUAL
    cursor.execute(
        "SELECT id_estado, timestampdiff(day,be.fecha,sysdate()) dias_estado, date_format(sysdate(),'%%Y-%%b-%%d %%h:%%i%%p') hoy \
                FROM boletas_estados be \
                WHERE be.id = (SELECT MAX(be2.id) FROM boletas_estados be2 \
                    WHERE be2.id_boleta = %s)",
        [id_boleta],
    )
    datos = cursor.fetchone()
    hoy = datos["hoy"]
    id_estado = datos["id_estado"]
    dias_estado = datos["dias_estado"]

    # MOVIMIENTOS
    cursor.execute(
        "select ifnull(sum(case when tipo=5 then monto else 0.0 end),0.0) revision \
            , ifnull(sum(case when tipo=2 then monto else 0.0 end),0.0) otros \
            , ifnull(sum(case when tipo=1 then monto else 0 end),0) pagos \
            , ifnull(sum(case when tipo=1 and medio=1 then monto else 0 end),0) efectivo \
            , ifnull(sum(case when tipo=1 and medio=2 then monto else 0 end),0) tarjeta \
            , ifnull(sum(case when tipo=1 and medio=3 then monto else 0 end),0) transferencia \
        from movimientos \
        where id_boleta=%s and estado=1",
        [id_boleta],
    )
    datos = cursor.fetchone()
    movimientos = datos
    monto_revision = float(movimientos["revision"])
    monto_otros_cargos = float(movimientos["otros"])
    monto_pagos = float(movimientos["pagos"])
    # VERIFICA SI TIENE COTIZACION ACTIVA
    cursor.execute(
        "select monto from boletas_cotizaciones b where id_boleta=%s and estado=1",
        [id_boleta],
    )
    datos = cursor.fetchone()
    monto_cotizacion = 0
    if datos is not None:
        monto_cotizacion = float(datos["monto"])
    # SI LA BOLETA HA SIDO RECHAZADA NO SE COBRA LA COTIZACION NI SE LE HACE EL DESCUENTO DE LA REVISION
    if rechazada == 1:
        monto_cotizacion = 0

    # DETALLE IMPUESTO POR SERVICIO
    cursor.execute(
        "select contenido from datos where id=14;",
    )
    dato_imp = cursor.fetchone()
    if dato_imp is not None:
        impuesto_por_servicio = float(dato_imp["contenido"])/100
    else:
        impuesto_por_servicio = 0

    # DETALLE IMPUESTO REPUESTOS NUEVOS
    cursor.execute(
        "select contenido from datos where id=6;",
    )
    dato_imp = cursor.fetchone()
    if dato_imp is not None:
        impuestoPorRepuestosNuevos = float(dato_imp["contenido"])/100
    else:
        impuestoPorRepuestosNuevos = 0
    
    # DETALLE IMPUESTO REPUESTOS USADOS
    cursor.execute(
        "select contenido from datos where id=7;",
    )
    dato_imp = cursor.fetchone()
    if dato_imp is not None:
        impuestoPorRepuestosUsados = float(dato_imp["contenido"])/100
    else:
        impuestoPorRepuestosUsados = 0

    # DETALLE DESCUENTOS
    cursor.execute(
        "select * from boletas_descuentos where id_boleta=%s and estado=1;",
        [id_boleta,],
    )
    datos = cursor.fetchall()
    datos_descuentos = 0
    mano_de_obra_descuento = 0
    repuestos_nuevos_descuento = 0
    repuestos_usados_descuento = 0
    bodegaje_descuento = 0
    total_descuentos = 0
    total_descuentos_con_impuestos = 0
    if datos is not None:
        datos_descuentos = datos
        for row in datos_descuentos:
            total_descuentos_con_impuestos+=float(row["monto"])
            if row["id_tipo_descuento"] == 1:  # Descuento Mano de Obra
                mano_de_obra_descuento += float(row["monto"])/(1+impuesto_por_servicio)
                total_descuentos += float(row["monto"])/(1+impuesto_por_servicio)
            if row["id_tipo_descuento"] == 2:  # Descuento Repuestos Nuevos
                repuestos_nuevos_descuento += float(row["monto"])/(1+impuestoPorRepuestosNuevos)
                total_descuentos += float(row["monto"])/(1+impuestoPorRepuestosNuevos)
            if row["id_tipo_descuento"] == 3:  # Descuento Repuestos Usados
                repuestos_usados_descuento += float(row["monto"])/(1+impuestoPorRepuestosUsados)
                total_descuentos += float(row["monto"])/(1+impuestoPorRepuestosUsados)
            if row["id_tipo_descuento"] == 4:  # Descuento Bodegaje
                bodegaje_descuento += float(row["monto"])
                total_descuentos += float(row["monto"])

    # VERIFICA BODEGAJE
    # BODEGAJE
    bodegaje_monto = 0
    bodegaje_monto_impuesto = 0
    bodegaje_dias = 0
    mano_de_obra = 0
    mano_de_obra_impuesto = 0
    tabla_factura = 0
    total_repuestos = 0
    total_repuestos_impuesto = 0
    total_otros_servicios = 0
    total_otros_servicios_impuesto = 0
    # if id_estado == 6 or id_estado == 7:  # SI ESTA EN FACTURAR O RECHAZADA
    # EXTRAE DATOS PARA FACTURA Y BODEGAJE
    cursor.execute(
        "select (select contenido from datos where id=3) rechazo, \
            (select contenido from datos where id=4) sin_retiro, \
            (select contenido from datos where id=5) bodegaje_tarifa, \
            (select contenido from datos where id=6) impuesto_rep_nuevo, \
            (select contenido from datos where id=7) impuesto_rep_usado, \
            (select contenido from datos where id=8) bodegaje_impuesto, \
            (select contenido from datos where id=9) impuesto_reparacion \
    from dual"
    )
    datos = cursor.fetchone()
    dias_rechazo = int(datos["rechazo"])
    dias_sin_retiro = int(datos["sin_retiro"])
    bodegaje_tarifa = float(datos["bodegaje_tarifa"])
    impuesto_rep_nuevo = float(datos["impuesto_rep_nuevo"])
    impuesto_rep_usado = float(datos["impuesto_rep_usado"])
    impuesto_reparacion = float(datos["impuesto_reparacion"])
    bodegaje_impuesto = float(
        datos["bodegaje_impuesto"]
    )  # GERARDO TORRES INDICO QUE NO TENIA IMPUESTO EL BODEGAJE 26/7/2020
    # CALCULO DE FACTURA OTROS SERVICIOS
    sql_otros_servicios = (
        'select "Otros Servicios", ifnull(sum(round(monto/(1+impuesto/100),2)),0) monto_sin_i, ifnull(sum(round(monto-monto/(1+impuesto/100),2)),0) monto_impuesto, 0 descuento from movimientos where id_boleta='
        + str(id_boleta)
        + " and tipo=2 and estado=1"
    )
    if tipo_cliente == 3:  # EXONERADO
        bodegaje_impuesto = 0
        impuesto_rep_nuevo = 0
        impuesto_rep_usado = 0
        impuesto_reparacion = 0
        sql_otros_servicios = (
            'select "Otros Servicios", ifnull(sum(round(monto,2)),0) monto_sin_i, 0 monto_impuesto, 0 descuento from movimientos where id_boleta='
            + str(id_boleta)
            + " and tipo=2 and estado=1"
        )
    # CALCULO DE BODEGAJE
    if id_estado == 6 and dias_estado > dias_sin_retiro:  # SIN RETIRO
        bodegaje_monto = (dias_estado - dias_sin_retiro) * bodegaje_tarifa
        bodegaje_dias = dias_estado - dias_sin_retiro
    elif id_estado == 7 and dias_estado > dias_rechazo:  # RECHAZO
        bodegaje_monto = (dias_estado - dias_rechazo) * bodegaje_tarifa
        bodegaje_dias = dias_estado - dias_rechazo
    else:
        if id_estado!=10:
            total_descuentos += -bodegaje_descuento
            bodegaje_descuento = 0
    bodegaje_monto = bodegaje_monto / (1 + bodegaje_impuesto / 100)
    bodegaje_monto_impuesto = (bodegaje_monto - bodegaje_impuesto) * (
        bodegaje_impuesto / 100
    )
    bodegaje_concepto = "Bodegaje (" + str(bodegaje_dias) + " días)"
    # CALCULO DE FACTURACION DE REPUESTOS
    # ,ifnull((select d.monto from boletas_descuentos d where d.id_boleta=r.id_boleta and d.id_tipo_descuento=2 and d.estado=1),0)*(1+%s)/100 descuento \
        
    cursor.execute(
        'select "Repuestos Nuevos" concepto, ifnull(sum(costo_factura*cantidad),0)/(1+%s/100) monto \
        , (ifnull(sum(costo_factura*cantidad),0)-ifnull((select d.monto from boletas_descuentos d where d.id_boleta=r.id_boleta and d.id_tipo_descuento=2 and d.estado=1),0)) \
            /(1+%s/100) * (%s/100) impuesto \
        ,ifnull((select d.monto/(1+%s/100) from boletas_descuentos d where d.id_boleta=r.id_boleta and d.id_tipo_descuento=2 and d.estado=1),0) descuento \
        from boletas_repuestos r where r.id_boleta=%s and r.estado=1 and r.tipo_repuesto=1 \
    union all \
        select "Repuestos Usados", ifnull(sum(costo_factura*cantidad),0)/(1+%s/100) monto \
        , (ifnull(sum(costo_factura*cantidad),0)-ifnull((select d.monto from boletas_descuentos d where d.id_boleta=r2.id_boleta and d.id_tipo_descuento=3 and d.estado=1),0)) \
          /(1+%s/100) * (%s/100) impuesto \
        ,ifnull((select d.monto/(1+%s/100) from boletas_descuentos d where d.id_boleta=r2.id_boleta and d.id_tipo_descuento=3 and d.estado=1),0) descuento \
        from boletas_repuestos r2 where r2.id_boleta=%s and r2.estado=1 and r2.tipo_repuesto=2 \
    union all '
        + sql_otros_servicios,
        [
            impuesto_rep_nuevo,
            impuesto_rep_nuevo,
            impuesto_rep_nuevo,
            impuesto_rep_nuevo,
            id_boleta,
            impuesto_rep_usado,
            impuesto_rep_usado,
            impuesto_rep_usado,
            impuesto_rep_usado,
            id_boleta,
        ],
    )
    datos = cursor.fetchall()
    total_repuestos_nuevos = 0
    total_repuestos_usados = 0
    total_repuestos = 0
    total_repuestos_impuesto = 0
    total_otros_servicios = 0
    total_otros_servicios_impuesto = 0
    total_repuestos_descuento = 0
    if datos is not None:
        tabla_factura = datos
        # TOTALES REPUESTOS y OTROS SERVICIOS
        for row in datos:
            if "Repuestos Nuevos" in row["concepto"]:
                total_repuestos_nuevos += float(row["monto"])
                total_repuestos += float(row["monto"])
                total_repuestos_impuesto += float(row["impuesto"])
                total_repuestos_descuento += float(row["descuento"])
            elif "Repuestos Usados" in row["concepto"]:
                total_repuestos_usados += float(row["monto"])
                total_repuestos += float(row["monto"])
                total_repuestos_impuesto += float(row["impuesto"])
                total_repuestos_descuento += float(row["descuento"])
            else:
                total_otros_servicios += float(row["monto"])
                total_otros_servicios_impuesto += float(row["impuesto"])
    # if total_repuestos_nuevos > repuestos_nuevos_descuento:
    #    repuestos_nuevos_descuento = 0
    #if total_repuestos_usados > repuestos_usados_descuento:
    #    repuestos_usados_descuento = 0
    total_repuestos_con_impuesto = total_repuestos + total_repuestos_impuesto - total_repuestos_descuento
    # MANO DE OBRA .. CALCULADA
    if cierre_anticipado == 0 and id_estado >= 4 and id_estado != 7:
        mano_de_obra = (monto_cotizacion - total_repuestos_con_impuesto - repuestos_nuevos_descuento*(1+impuestoPorRepuestosNuevos) - repuestos_usados_descuento*(1+impuestoPorRepuestosUsados)) / (
            1 + impuesto_reparacion / 100
        )  # MANO DE OBRA .. CALCULADA
        mano_de_obra_impuesto = (mano_de_obra - mano_de_obra_descuento) * (
            impuesto_reparacion / 100
        )  # IMPUESTO MANO DE OBRA .. CALCULADA
        # SI HAY ALGUN REPUESTO QUE SOBREPASE LA COTIZACION
        if mano_de_obra < 0:
            mano_de_obra = 0
            mano_de_obra_impuesto = 0
        
    else:
        mano_de_obra = monto_revision / (1 + impuesto_reparacion / 100)
        mano_de_obra_impuesto = (
            (mano_de_obra - mano_de_obra_descuento) * impuesto_reparacion / 100
        )

    # PARA BODEGAJE, VERIFICA SI YA EXISTE UN COMPROBANTE PARA NO DAR UN CALCULO NO REAL
    cursor.execute(
        'select id from boletas_comprobantes where id_boleta=%s and estado=1',
        [id_boleta,],
    )
    datos = cursor.fetchone()
    if datos is not None:
        cursor.execute(
            'select concepto, bcd.monto, bcd.impuestos \
            from boletas_comprobantes bc left join boletas_comprobantes_detalle bcd on bcd.id_comprobante=bc.id \
            where id_boleta=%s and bc.estado=1 and bcd.concepto like "Bodegaje%%"',
            [id_boleta,],
        )
        datos = cursor.fetchone()
        if datos is not None:
            bodegaje_concepto = datos["concepto"]
            bodegaje_monto = datos["monto"]
            bodegaje_monto_impuesto = datos["impuestos"]
        else:
            bodegaje_concepto = ""
            bodegaje_monto = 0
            bodegaje_monto_impuesto = 0

    # CALCULO DEL SALDO
    if (
        cierre_anticipado != 1 and id_estado >= 4 and id_estado != 7 and rechazada == 0
    ):  # SI NO TIENE CIERRE ANTICIPADO o RECHAZO, DEBE CONTAR EL MONTO DE COTIZACION
        saldo = (
            monto_pagos
            - monto_otros_cargos
            - monto_cotizacion
            - (bodegaje_monto + bodegaje_monto_impuesto)
            + total_descuentos_con_impuestos
            #+ (bodegaje_descuento * (1 + bodegaje_impuesto/100))
            #//+ (mano_de_obra_descuento * (1 + impuesto_reparacion/100))
        )
    else:
        saldo = (
            monto_pagos
            - monto_revision
            - monto_otros_cargos
            - (bodegaje_monto + bodegaje_monto_impuesto)
        )
    """ print(saldo)
    saldo = -(
        mano_de_obra + total_repuestos + total_otros_servicios + bodegaje_monto
        ) + (
        total_descuentos
        + mano_de_obra_impuesto
        + total_repuestos_impuesto
        + total_otros_servicios_impuesto
        + bodegaje_monto_impuesto
        - monto_pagos
    ) """
    # DETALLE DE MOVIMIENTOS DE PAGOS Y CARGOS
    tabla_movimientos = datos_movimientos(
        mysql, id_boleta, id_estado, cierre_anticipado
    )
    cursor.close()
    datos = {
        "saldo": saldo,
        "monto_revision": monto_revision,
        "monto_otros_cargos": monto_otros_cargos,
        "monto_total_bodegaje_descuento" : bodegaje_descuento * (1 + bodegaje_impuesto/100),
        "monto_total_mano_de_obra_descuento" : mano_de_obra_descuento * (1 + impuesto_reparacion/100),  
        "monto_pagos": monto_pagos,
        "monto_cotizacion": monto_cotizacion,
        "monto_efectivo": float(movimientos["efectivo"]),
        "monto_tarjeta": float(movimientos["tarjeta"]),
        "monto_transferencia": float(movimientos["transferencia"]),
        "tabla_movimientos": tabla_movimientos,
        "bodegaje_monto": bodegaje_monto,
        "bodegaje_descuento": bodegaje_descuento,
        "bodegaje_monto_impuesto": bodegaje_monto_impuesto,
        "bodegaje_concepto": bodegaje_concepto,
        "bodegaje_dias": bodegaje_dias,
        "hoy": hoy,
        "mano_de_obra": mano_de_obra,
        "mano_de_obra_descuento": mano_de_obra_descuento,
        "mano_de_obra_impuesto": mano_de_obra_impuesto,
        "tabla_factura": tabla_factura,
        "total_repuestos": total_repuestos,
        "total_repuestos_impuesto": total_repuestos_impuesto,
        "total_repuestos_con_impuesto": total_repuestos_con_impuesto,
        "total_otros_servicios": total_otros_servicios,
        "total_otros_servicios_impuesto": total_otros_servicios_impuesto,
        "total_monto_factura": mano_de_obra
        + total_repuestos
        + total_otros_servicios
        + bodegaje_monto,
        "total_monto_factura_impuesto": mano_de_obra_impuesto
        + total_repuestos_impuesto
        + total_otros_servicios_impuesto
        + bodegaje_monto_impuesto,
        "tipo_cliente": tipo_cliente,
        "total_repuestos_nuevos": total_repuestos_nuevos,
        "total_repuestos_usados": total_repuestos_usados,
        "datos_descuentos": datos_descuentos,
        "total_descuentos": total_descuentos,
        "total_descuentos_con_impuestos": total_descuentos_con_impuestos,
        "total_factura": mano_de_obra
        + total_repuestos
        + total_otros_servicios
        + bodegaje_monto
        - total_descuentos
        + mano_de_obra_impuesto
        + total_repuestos_impuesto
        + total_otros_servicios_impuesto
        + bodegaje_monto_impuesto
    }
    return datos


def kapp_usuarios_disponibles(mysql, application_id):
    # CONSULTA SI HAY LICENCIAS DISPONIBLES
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute(
        "select licencias-(select count(1) usuarios_activos \
            from kapps_db.accounts where kapp_id=k.id and id<>3 and estado=1) disponibles \
                from kapps_db.kapps k where id=%s",
        [application_id],
    )
    datos = cursor.fetchone()
    return datos["disponibles"]
