from flask import render_template, session, jsonify
import os
import MySQLdb
from decimal import Decimal
import consultas_base
import inventario


def principal(tienda_accion, tienda_accion2, formulario, mysql):
    if tienda_accion == 1:  # INICIO
        datos_carrito = carrito(mysql)
        datos_disponibilidad = inventario.disponibilidad_producto(mysql, "0")
        modificable = 1
        return render_template(
            "tienda.html",
            tienda_accion=tienda_accion,
            datos_carrito=datos_carrito,
            datos_disponibilidad=datos_disponibilidad,
            modificable=modificable,
            formulario=formulario,
        )

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SET lc_time_names = "es_ES"')
    if tienda_accion == 2:  # CARRITO
        datos_carrito = carrito(mysql)
        cursor.close()
        modificable = 1
        return render_template(
            "tienda_carrito.html", datos_carrito=datos_carrito, modificable=modificable
        )
    if tienda_accion == 3:  # DISPONIBILIDAD DE UN PRODUCTO
        datos_disponibilidad = inventario.disponibilidad_producto(
            mysql, formulario["codigo_producto"]
        )
        cursor.close()
        return datos_disponibilidad
    if tienda_accion == 4:  # INGRESO A VENTA (GENERAR RECIBO)
        # VALIDA DISPONIBILIDAD EN INVENTARIO
        carrito_resultado = carrito(mysql)
        if carrito_resultado["error_disponibilidad"] == 0:
            cursor.execute(
                "insert into venta_ventas (id_cliente, monto_sin_impuestos, impuestos, id_usuario) \
                values(%s,%s,%s,%s)",
                [
                    formulario["id_cliente"],
                    carrito_resultado["monto"],
                    carrito_resultado["impuestos"],
                    session["id"],
                ],
            )
            id_venta = cursor.lastrowid
            # REGISTRA LOS MOVIMIVIENTOS EN EL INVENTARIO
            for row in carrito_resultado["elementos"]:
                impuesto = (
                    row["precio"]
                    - (row["precio"] / (1 + float(row["pct_impuesto"]) / 100))
                ) * int(row["unidades"])
                precio_total = float((row["precio"] * row["unidades"])) - impuesto
                resultado = venta_unitaria(
                    mysql,
                    row["codigo_producto"],
                    row["id_estado_producto"],
                    row["unidades"],
                    2,
                    id_venta,
                    precio_total,
                    impuesto,
                )
            # REGISTRA LOS PAGOS EN MOVIMIENTOS
            cursor.execute(
                "insert into movimientos (monto, tipo, medio, id_usuario, concepto, estado, id_venta) \
                select monto, 10, medio, id_usuario, 'Venta', 1, %s from venta_pre_pagos where id_usuario=%s",
                [id_venta, session["id"]],
            )
            # LIMPIA LOS PAGOS
            cursor.execute(
                "delete from venta_pre_pagos where id_usuario=%s", [session["id"]]
            )
            # LIMPIA EL CARRITO
            cursor.execute(
                "delete from venta_pre where id_usuario=%s",
                [
                    session["id"],
                ],
            )
            mysql.connection.commit()
            carrito_resultado = carrito(mysql)
            modificable = 1
            render_carrito = render_template(
                "tienda_carrito.html",
                datos_carrito=carrito_resultado,
                modificable=modificable,
            )
            # DATOS DEL CLIENTE PARA LOS BOTONES DE LA VENTA
            cursor.execute(
                "select correo, telefono from tx_clientes where id=%s",
                [
                    formulario["id_cliente"],
                ],
            )
            datos_cliente = cursor.fetchone()
            render_botones = render_template(
                "tienda.html",
                display_venta_botones=1,
                id_venta=id_venta,
                correo=datos_cliente["correo"],
                telefono="506" + str(datos_cliente["telefono"]),
            )
            cursor.close()
            return jsonify(
                resultado="OK", carrito=render_carrito, botones=render_botones
            )

        else:
            return "E:DISPONIBILIDAD"
    if tienda_accion == 5:  # INGRESO A CARRITO / A BOLETA
        modificable = 1
        if formulario["repuesto_boleta"] == "0":  # PRODUCTO EN TIENDA
            cursor.execute(
                "insert into venta_pre (codigo_producto, unidades, estado_producto, id_usuario) \
            values (%s,%s,%s,%s)",
                [
                    formulario["codigo_producto"],
                    formulario["unidades"],
                    formulario["estado"],
                    session["id"],
                ],
            )
            mysql.connection.commit()
            datos_carrito = carrito(mysql)
            cursor.close()
            return render_template(
                "tienda_carrito.html",
                datos_carrito=datos_carrito,
                modificable=modificable,
            )
        if formulario["repuesto_boleta"] == "1":  # PRODUCTO COMO REPUESTO PARA BOLETA
            # VALIDA DISPONIBILIDAD EN INVENTARIO
            datos = inventario.disponibilidad_producto(
                mysql, formulario["codigo_producto"]
            )
            if formulario["estado"] == "1":
                unidades_inventario = datos["unidades_nuevas"]
                precio_inventario = datos["precio_nuevo"]
                costo_inventario = datos["precio_nuevo_taller"]
            elif formulario["estado"] == "2":
                unidades_inventario = datos["unidades_usadas"]
                precio_inventario = datos["precio_usado"]
                costo_inventario = datos["precio_usado_taller"]
            # COMPARA PARA PROSEGUIR CON EL REGISTRO
            if unidades_inventario >= int(formulario["unidades"]):
                cursor.execute(
                    "insert into boletas_repuestos (id_boleta, id_repuesto, costo, costo_factura, cantidad, tipo_repuesto,id_usuario,estado, proveedor, info) \
                    values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                    [
                        formulario["id_boleta"],
                        0,
                        costo_inventario,
                        precio_inventario,
                        formulario["unidades"],
                        formulario["estado"],
                        session["id"],
                        1,
                        "ET TIENDA",
                        formulario["codigo_producto"],
                    ],
                )
                # REGISTRA EL MOVIMIVIENTO EN EL INVENTARIO
                resultado = venta_unitaria(
                    mysql,
                    formulario["codigo_producto"],
                    int(formulario["estado"]),
                    int(formulario["unidades"]),
                    3,
                    formulario["id_boleta"],
                    cursor.lastrowid,
                )
                mysql.connection.commit()
                cursor.close()
                return resultado
            else:
                return "NOT-ENOUGH"
    if tienda_accion == 6:  # VACIAR CARRITO
        cursor.execute(
            "delete from venta_pre where id_usuario=%s",
            [
                session["id"],
            ],
        )
        mysql.connection.commit()
        datos_carrito = carrito(mysql)
        cursor.close()
        modificable = 1
        return render_template(
            "tienda_carrito.html", datos_carrito=datos_carrito, modificable=modificable
        )
    if tienda_accion == 7:  # ELIMINAR ELEMENTO DEL CARRITO
        if formulario["estado_producto"] == "NUEVO":
            estado = 1
        if formulario["estado_producto"] == "USADO":
            estado = 2
        cursor.execute(
            "delete from venta_pre where id_usuario=%s and codigo_producto=%s and estado_producto=%s",
            [session["id"], formulario["codigo_producto"], estado],
        )
        mysql.connection.commit()
        datos_carrito = carrito(mysql)
        cursor.close()
        modificable = 1
        return render_template(
            "tienda_carrito.html", datos_carrito=datos_carrito, modificable=modificable
        )
    if tienda_accion == 8:  # PRESENTACION DE CARRITO PARA RECIBO
        datos_carrito = carrito(mysql)
        cursor.close()
        modificable = 0
        return render_template(
            "tienda_carrito.html", datos_carrito=datos_carrito, modificable=modificable
        )
    if tienda_accion == 9:  # VENTA PRE SALDO Y PAGOS
        datos_carrito = carrito(mysql)
        cursor.execute(
            'select monto \
            , case when medio=0 then "" when medio=1 then "Efectivo" when medio=2 then "Tarjeta Cred/Deb" when medio=3 then "Transferencia" end medio \
            , id from venta_pre_pagos where id_usuario=%s',
            [session["id"]],
        )
        pagos = cursor.fetchall()
        total_pagos = 0
        for row in pagos:
            total_pagos += row["monto"]
        saldo = str(datos_carrito["monto_a_pagar"] - total_pagos)
        return jsonify(pagos=pagos, saldo=saldo)
    if tienda_accion == 10:  # REALIZAR PAGO
        cursor.execute(
            "insert into venta_pre_pagos (id_usuario, monto, medio) values (%s,%s,%s)",
            [session["id"], formulario["monto"], formulario["medio"]],
        )
        mysql.connection.commit()
        return "OK"
    if tienda_accion == 11:  # ANULAR PAGO
        cursor.execute(
            "delete from venta_pre_pagos where id_usuario=%s and id=%s",
            [session["id"], formulario["id_pago"]],
        )
        mysql.connection.commit()
        return "OK"
    if tienda_accion == 12:  # VER VENTA
        datos = venta_detalle(mysql, formulario["id_venta"])
        cursor.close()
        return render_template(
            "tienda_venta.html",
            datos=datos,
            display_venta_botones=1,
            id_venta=formulario["id_venta"],
            correo=datos["datos_venta"]["correo"],
            telefono="506" + str(datos["datos_venta"]["telefono"]),
        )
    if tienda_accion == 13:  # DATOS PARA DEVOLUCION
        datos = venta_devolucion(
            mysql,
            formulario["id_venta"],
            formulario["codigo_producto"],
            formulario["id_estado"],
            formulario["unidades"],
            formulario["comentario"],
        )
        cursor.close()
        return datos


def carrito(mysql):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute(
        "select v.codigo_producto, sum(v.unidades) unidades \
                ,ifnull((select sum(disponibilidad) from inv_lotes where codigo_producto=v.codigo_producto \
                    and id_estado=v.estado_producto and disponibilidad>0 and disponible=1),0) disponibilidad \
            ,ifnull((select precio_venta from inv_lotes \
                where id = (select max(id) from inv_lotes where codigo_producto=v.codigo_producto \
                    and id_estado=v.estado_producto and disponibilidad>0 and disponible=1)),0) precio \
            , p.nombre, m.nombre marca \
            ,  case when v.estado_producto=1 then 'NUEVO' \
                    when v.estado_producto=2 then 'USADO' end estado_producto \
            ,  case when v.estado_producto=1 then (select contenido from datos where id = 6) \
					when v.estado_producto=2 then (select contenido from datos where id = 7) \
				end pct_impuesto \
            , v.estado_producto id_estado_producto \
            from venta_pre v left join inv_productos p on p.id = v.codigo_producto \
                left join marcas m on m.id=p.id_marca \
            where v.id_usuario=%s \
            group by v.codigo_producto , p.nombre, m.nombre, case when v.estado_producto=1 then 'NUEVO' \
                    when v.estado_producto=2 then 'USADO' end, v.estado_producto \
                    , case when v.estado_producto=1 then (select contenido from datos where id = 6) \
					when v.estado_producto=2 then (select contenido from datos where id = 7) end \
            ",
        [
            session["id"],
        ],
    )
    elementos = cursor.fetchall()
    conteo = 0
    monto_total = 0
    error_disponibilidad = 0
    impuestos = 0
    for row in elementos:
        conteo += row["unidades"]
        monto_total += row["precio"] * row["unidades"]
        impuestos += (
            row["precio"] - (row["precio"] / (1 + float(row["pct_impuesto"]) / 100))
        ) * int(row["unidades"])
        if row["unidades"] > row["disponibilidad"]:
            error_disponibilidad = 1
    cursor.close()
    datos = {
        "elementos": elementos,
        "conteo": conteo,
        "monto_a_pagar": monto_total,
        "monto": round(Decimal(monto_total) - Decimal(impuestos), 2),
        "impuestos": round(impuestos, 2),
        "error_disponibilidad": error_disponibilidad,
    }
    return datos


def venta_detalle(mysql, id_venta):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute(
        "select l.codigo_producto, sum(ll.unidades) unidades, sum(ll.monto_sin_impuestos) monto_sin_impuestos, sum(ll.impuestos) impuestos \
            , p.nombre, p.modelo, m.nombre marca \
            , pe.descripcion estado_producto, pe.id estado_id \
            , case when timestampdiff(day,ll.fecha,sysdate())<=p.garantia then 1 else 0 end en_garantia \
            , ifnull(sum(ll2.unidades),0) unidades_devueltas, ifnull(sum(ll2.monto_devoluciones),0) monto_devoluciones, ifnull(sum(ll2.monto_devoluciones_impuestos),0) monto_devoluciones_impuestos \
            from inv_lotes_log ll left join inv_lotes l on l.id=ll.id_lote \
                left join inv_productos p on p.id = l.codigo_producto \
                left join marcas m on m.id = p.id_marca \
                left join inv_productos_estados pe on pe.id = l.id_estado \
                left join (select id_lote, sum(unidades) unidades, sum(monto_sin_impuestos) monto_devoluciones, sum(impuestos) monto_devoluciones_impuestos from inv_lotes_log ll2 where ll2.tipo=5 and ll2.parametro=%s group by id_lote) ll2 \
					on ll2.id_lote=ll.id_lote \
            where ll.tipo=2 and ll.parametro=%s \
            group by l.codigo_producto, p.nombre, p.modelo, m.nombre \
            , pe.descripcion, pe.id, case when timestampdiff(day,ll.fecha,sysdate())<=p.garantia then 1 else 0 end",
        [
            id_venta,id_venta,
        ],
    )
    elementos = cursor.fetchall()
    conteo = 0
    monto_devoluciones = 0
    monto_devoluciones_impuestos = 0
    for regs in elementos:
        conteo += regs["unidades"]
        monto_devoluciones+=regs["monto_devoluciones"]
        monto_devoluciones_impuestos+=regs["monto_devoluciones_impuestos"]
    # DATOS VENTA
    cursor.execute(
        "select vv.id, vv.fecha, vv.monto_sin_impuestos, impuestos, username, cl.id id_cliente, concat(nombres, ' ', apellidos) cliente_nombre \
        , cl.n_documento, cl.tipo_documento, cl.correo, cl.telefono \
	        from venta_ventas vv left join kapps_db.accounts a on a.id=vv.id_usuario \
                left join tx_clientes cl on cl.id=vv.id_cliente \
            where vv.id=%s",
        [
            id_venta,
        ],
    )
    datos_venta = cursor.fetchone()
    cursor.close()
    datos = {"elementos": elementos, "conteo": conteo, "datos_venta": datos_venta, "monto_devoluciones": monto_devoluciones,"monto_devoluciones_impuestos":monto_devoluciones_impuestos}
    return datos


def venta_unitaria(
    mysql,
    codigo_producto,
    estado_producto,
    unidades_requeridas,
    tipo_transaccion,
    parametro,
    parametro2="",
    parametro3="",
):
    # REVISAR EXISTENCIA
    formulario = {"codigo_producto": codigo_producto, "estado": estado_producto}
    datos = inventario.principal(2, 3, formulario, 0, mysql)
    unidades_originales = unidades_requeridas
    if unidades_requeridas > datos["unidades"]:
        return "NOT-ENOUGH"
    else:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        unidades_transaccion = 0
        while True:
            cursor.execute(
                "select disponibilidad, id \
                ,  case when id_estado=1 then (select contenido from datos where id = 6) \
					when id_estado=2 then (select contenido from datos where id = 7) \
				    end pct_impuesto \
                    from inv_lotes where id = (select min(id) from inv_lotes where codigo_producto=%s \
                                        and id_estado=%s and disponibilidad>0 and disponible=1)",
                [codigo_producto, estado_producto],
            )
            datos_lote = cursor.fetchone()
            if unidades_requeridas > datos_lote["disponibilidad"]:
                unidades_requeridas = unidades_requeridas - datos_lote["disponibilidad"]
                unidades_transaccion = datos_lote["disponibilidad"]
                nuevo_unidades_lote = 0
                nuevo_estado_lote = 0
            else:
                nuevo_unidades_lote = datos_lote["disponibilidad"] - unidades_requeridas
                unidades_transaccion = unidades_requeridas
                unidades_requeridas = 0
                nuevo_estado_lote = 1
            cursor.execute(
                "update inv_lotes set disponibilidad = %s, disponible=%s where id = %s",
                [nuevo_unidades_lote, nuevo_estado_lote, datos_lote["id"]],
            )
            if tipo_transaccion == 2:  # VENTA
                monto_sin_impuestos = (
                    parametro2
                    / float(unidades_originales)
                    * float(unidades_transaccion)
                )
                impuestos = (
                    parametro3
                    / float(unidades_originales)
                    * float(unidades_transaccion)
                )
                cursor.execute(
                    "insert into inv_lotes_log (id_lote, tipo, unidades, id_usuario, parametro, monto_sin_impuestos, impuestos) \
                        values (%s,%s,%s,%s,%s,%s,%s)",
                    [
                        datos_lote["id"],
                        tipo_transaccion,
                        unidades_transaccion,
                        session["id"],
                        parametro,
                        monto_sin_impuestos,
                        impuestos,
                        # datos_lote["costo_unitario"]
                    ],
                )
            else:  # TALLER
                # Precio ACTUAL
                cursor.execute(
                    "select precio_taller from inv_lotes \
                        where id = (select max(id) from inv_lotes \
                                    where codigo_producto=%s and id_estado=%s and disponibilidad>0)",
                    [codigo_producto, estado_producto],
                )
                resultado = cursor.fetchone()
                precio = resultado["precio_taller"]
                monto_sin_impuestos = (precio * float(unidades_transaccion)) / (
                    1 + (float(datos_lote["pct_impuesto"])) / 100
                )
                impuestos = (
                    monto_sin_impuestos * (float(datos_lote["pct_impuesto"])) / 100
                )
                cursor.execute(
                    "insert into inv_lotes_log (id_lote, tipo, unidades, id_usuario, parametro, comentario, monto_sin_impuestos, impuestos ) \
                        values (%s,%s,%s,%s,%s,%s,%s,%s)",
                    [
                        datos_lote["id"],
                        tipo_transaccion,
                        unidades_transaccion,
                        session["id"],
                        parametro,
                        parametro2,
                        monto_sin_impuestos,
                        impuestos,
                    ],
                )
            if unidades_requeridas == 0:
                break
        mysql.connection.commit()
        cursor.close()
        return "OK"


def venta_devolucion(
    mysql, id_venta, codigo_producto, estado_producto, unidades_requeridas, comentario
):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    unidades_transaccion = 0
    unidades_requeridas = int(unidades_requeridas)
    cursor.execute(
        "select ll.id_lote id, ll.unidades unidades, monto_sin_impuestos/ll.unidades monto_sin_impuestos, impuestos/ll.unidades impuestos \
            from inv_lotes_log ll left join inv_lotes l on l.id=ll.id_lote \
            where ll.tipo=2 and ll.parametro=%s and l.codigo_producto=%s and l.id_estado=%s \
            order by l.fecha_ingreso desc",
        [id_venta, codigo_producto, estado_producto],
    )
    datos_lotes_venta = cursor.fetchall()
    for r_lotes in datos_lotes_venta:
        print(str(unidades_requeridas) + " - " + str(r_lotes["unidades"]))
        if int(unidades_requeridas) > int(r_lotes["unidades"]):
            print("1x")
            unidades_transaccion = int(r_lotes["unidades"])
        else:
            print("2x")
            unidades_transaccion = unidades_requeridas
        cursor.execute(
            "update inv_lotes set disponibilidad = disponibilidad + %s, disponible=1 where id = %s",
            [unidades_transaccion, r_lotes["id"]],
        )
        print(cursor._executed)
        unidades_requeridas -= unidades_transaccion
        cursor.execute(
            "insert into inv_lotes_log (id_lote, tipo, unidades, id_usuario, parametro, comentario, monto_sin_impuestos, impuestos) \
                values (%s,%s,%s,%s,%s,%s,%s,%s)",
            [
                r_lotes["id"],
                5,
                unidades_transaccion,
                session["id"],
                id_venta,
                comentario,
                r_lotes["monto_sin_impuestos"] * unidades_transaccion,
                r_lotes["impuestos"] * unidades_transaccion,
            ],
        )
        if unidades_requeridas == 0:
            break
    mysql.connection.commit()
    cursor.close()
    return "OK"
