from flask import render_template, session, jsonify
import os
import MySQLdb
import consultas_base
import tienda

FOLDER_INV_IMAGENES = "static/inv_imagenes/"


def principal(inv_accion, inv_accion2, formulario, archivos, mysql):
    mensaje = ""
    marcas = []
    proveedores = []
    datos = []
    nuevo_codigo=""
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SET lc_time_names = "es_ES"')
    if inv_accion==1:
        cursor.execute("SELECT nombre FROM proveedores where estado=1")
        proveedores = cursor.fetchall()
    if inv_accion == 3:  # PRODUCTO
        if inv_accion2 == 0:  # FORMULARIO INICIAL
            cursor.execute("SELECT nombre FROM marcas where estado=1")
            marcas = cursor.fetchall()
        if inv_accion2 == 1:  # CREAR PRODUCTO
            cursor.execute("SELECT nombre FROM marcas where estado=1")
            marcas = cursor.fetchall()
            # EXTRAE EL ID DE LA MARCA
            cursor.execute(
                "SELECT id id_marca FROM marcas WHERE nombre = %s",
                [formulario["marca"].upper().strip()],
            )
            datos = cursor.fetchone()
            id_marca = datos["id_marca"]
            # VERIFICA SI EXISTE EL NOMBRE / MARCA / MODELO
            resultado = consultas_base.un_dato(
                mysql,
                1,
                "inv_productos",
                "nombre = '"
                + formulario["nombre"].upper().strip()
                + "'"
                + " and id_marca="
                + str(id_marca)
                + " and modelo="
                + "'"
                + formulario["modelo"].upper().strip()
                + "'"
                + " and estado=1",
                "consulta",
            )
            if resultado == "0":  # EL NOMBRE NO EXISTE Y SE PUEDE CREAR
                # SE GENERA CODIGO
                cursor.execute(
                    "select count(1) maximo from inv_productos",
                )
                datos = cursor.fetchone()
                nuevo_codigo = datos["maximo"] + 1
                if int(formulario["categoria"]) == 1:
                    nuevo_codigo = "A" + ("0000" + str(nuevo_codigo))[-5:]
                if int(formulario["categoria"]) == 2:
                    nuevo_codigo = "R" + ("0000" + str(nuevo_codigo))[-5:]
                print(nuevo_codigo)
                flag_archivos = [0, 0, 0]
                # for idx, fs in enumerate(archivos):
                #     if fs.filename != "":
                #         flag_archivos[idx] = 1
                if archivos['inv_file1'].filename != "":
                    flag_archivos[0] = 1
                if archivos['inv_file2'].filename != "":
                    flag_archivos[1] = 1
                if archivos['inv_file3'].filename != "":
                    flag_archivos[2] = 1
                
                cursor.execute( "insert into inv_productos \
                    (id,nombre,modelo, descripcion, id_categoria, img1, img2, img3, dias_estimados, garantia, cabys, id_usuario_ingresa, id_marca) \
                    values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                    [
                        nuevo_codigo,
                        formulario["nombre"].upper().strip(),
                        formulario["modelo"].upper().strip(),
                        formulario["descripcion"].strip(),
                        formulario["categoria"],
                        flag_archivos[0],
                        flag_archivos[1],
                        flag_archivos[2],
                        formulario["disponibilidad"],
                        formulario["garantia"],
                        formulario["cabys"],
                        session["id"],
                        id_marca,
                    ],
                )
                mysql.connection.commit()
                if archivos['inv_file1'].filename != "":
                    archivos['inv_file1'].save(os.path.join(FOLDER_INV_IMAGENES,nuevo_codigo + "_1" + archivos['inv_file1'].filename[-4:],))
                if archivos['inv_file2'].filename != "":
                    archivos['inv_file2'].save(os.path.join(FOLDER_INV_IMAGENES,nuevo_codigo + "_2" + archivos['inv_file2'].filename[-4:],))
                if archivos['inv_file3'].filename != "":
                    archivos['inv_file3'].save(os.path.join(FOLDER_INV_IMAGENES,nuevo_codigo + "_3" + archivos['inv_file3'].filename[-4:],))
                mensaje = (
                    "El producto <b>"
                    + formulario["nombre"].upper().strip()
                    + "</b> fue agregado satisfactoriamente en el inventario con el código <b>"
                    + nuevo_codigo
                    + "</b>"
                )
                # return "OK-PRODUCTO CREADO"
            elif resultado == "1":  # EL NOMBRE YA EXISTE Y NO SE PUEDE CREAR
                mensaje = (
                    "Error al crear el producto <b>"
                    + formulario["nombre"].upper().strip()
                    + "</b><br>El producto ya existe en el inventario."
                )
            else:  # OTRO CODIGO DE ERROR Y NO SE PUEDE CREAR (Revisar modulo de consulta en consultas_base.py)
                mensaje = (
                    "Error al crear el producto <b>"
                    + formulario["nombre"].upper().strip()
                    + "</b><br>Por favor, repórtelo al administrador."
                )
        if inv_accion2 == 2:  # CONSULTA NOMBRE Y CATALOGOS
            cursor.execute(
                "SELECT id id_marca FROM marcas WHERE nombre = %s",
                [formulario["marca"].upper().strip()],
            )
            datos = cursor.fetchone()
            if datos is None:
                cursor.close()
                return "NO-MARCA"
            else:
                # EXTRAE EL ID DE LA MARCA
                cursor.execute(
                    "SELECT id id_marca FROM marcas WHERE nombre = %s",
                    [formulario["marca"].upper().strip()],
                )
                datos = cursor.fetchone()
                id_marca = datos["id_marca"]
                # verificar de duplicado (solo cuando se modifica un producto)
                complemento = ""
                if int(formulario["tipo"]) == 2:
                    complemento = " and id <> '"+ formulario["codigo_producto"] + "'"
                # VERIFICA SI EXISTE EL NOMBRE / MARCA / MODELO
                resultado = consultas_base.un_dato(
                    mysql,
                    1,
                    "inv_productos",
                    "nombre = '"
                    + formulario["nombre"].upper().strip()
                    + "'"
                    + " and id_marca="
                    + str(id_marca)
                    + " and modelo="
                    + "'"
                    + formulario["modelo"].upper().strip()
                    + "' and estado=1"
                    + complemento,
                    "consulta",
                )
                return resultado
        if inv_accion2 == 3:  # CONSULTA LISTA DE PRODUCTOS (POR SUPER CAMPO)
            cursor.execute(
                "select i.*, i.nombre producto, m.nombre marca, c.nombre categoria \
                    FROM inv_productos i left join marcas m on i.id_marca=m.id \
                    left join inv_categorias c on c.id=i.id_categoria \
                WHERE (i.id LIKE %s \
                        OR i.nombre like %s \
                        OR modelo like %s \
                        OR m.nombre like %s \
                        ) and i.estado=1 \
                LIMIT 15",
                [
                    "%" + formulario["cadena"].upper().strip() + "%",
                    "%" + formulario["cadena"].upper().strip() + "%",
                    "%" + formulario["cadena"].upper().strip() + "%",
                    "%" + formulario["cadena"].upper().strip() + "%",
                ],
            )

            resultado = cursor.fetchall()
            cursor.close()
            return jsonify(resultado=resultado)
        if inv_accion2 == 4:  # ACTUALIZAR PRODUCTO
            # EXTRAE EL ID DE LA MARCA
            cursor.execute(
                "SELECT id id_marca FROM marcas WHERE nombre = %s",
                [formulario["marca"].upper().strip()],
            )
            datos = cursor.fetchone()
            id_marca = datos["id_marca"]
            # ACTUALIZA REGISTRO
            cursor.execute(
                "UPDATE inv_productos set nombre=%s, id_marca=%s, modelo=%s, id_categoria=%s \
                    ,descripcion=%s, garantia=%s, dias_estimados=%s, cabys=%s \
                WHERE id = %s",
                [formulario["nombre"].upper().strip(),
                id_marca,
                formulario["modelo"].upper().strip(),
                formulario["categoria"],
                formulario["descripcion"].upper().strip(),
                formulario["garantia"],
                formulario["disponibilidad"],
                formulario["cabys"],
                formulario["codigo"]],
            )
            mysql.connection.commit()
            return "OK"
        if inv_accion2 == 5:
            print("++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
            print(archivos)
            return "OK"
    if inv_accion == 2:  # LOTE
        if inv_accion2 == 1:  # CREAR LOTE
            proveedor=formulario["proveedor"].upper().strip()
            cursor.execute("SELECT id id_proveedor FROM proveedores WHERE nombre = %s", [proveedor])
            datos = cursor.fetchone()
            if datos is None:
                cursor.close()
                return "NO-PROVEEDOR"
            else:
                id_proveedor = datos["id_proveedor"]
                cursor.execute(
                "insert into inv_lotes \
                (codigo_producto, factura, monto_factura, fecha_factura, unidades, id_estado, id_proveedor, precio_venta, disponibilidad, id_usuario_ingresa, flete, aduana, costo_unitario, ubicacion, precio_taller) \
                values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                [
                    formulario["codigo_producto"].upper().strip(),
                    formulario["factura"].upper().strip(),
                    formulario["monto_factura"],
                    formulario["fecha_factura"],
                    formulario["unidades"],
                    formulario["estado"],
                    id_proveedor,
                    formulario["precio_venta"],
                    formulario["unidades"],
                    session["id"],
                    formulario["flete"],
                    formulario["aduana"],
                    formulario["costo_unitario"],
                    formulario["ubicacion"],
                    formulario["precio_a_taller"],
                ],
                )
                mysql.connection.commit()
                cursor.close()
                return "OK"
        if inv_accion2 == 2:  # CONSULTA LOTES PARA UN PRODUCTO
            cursor.execute(
                'select id lote, date_format(fecha_ingreso,"%%Y-%%b-%%d %%h:%%i%%p") ingreso \
                    , concat(disponibilidad," / ",unidades) unidades \
                    , case when id_estado=1 then "Nuevo" when id_estado=2 then "Usado" end "Estado", precio_venta precio \
                FROM inv_lotes WHERE codigo_producto = %s and disponibilidad > 0 order by disponible desc \
                LIMIT 15',
                [
                    formulario["codigo_producto"],
                ],
            )
            resultado = cursor.fetchall()
            cursor.close()
            return jsonify(resultado=resultado)
        if inv_accion2 == 3:  # CONSULTA DISPONIBILIDAD PARA UN PRODUCTO
            cursor.execute(
                "select ifnull(sum(disponibilidad),0) unidades , count(1) lotes \
                 from inv_lotes where codigo_producto=%s and id_estado=%s and disponible=1 and disponibilidad>0",
                [formulario["codigo_producto"], formulario["estado"]],
            )
            resultado = cursor.fetchone()
            cursor.close()
            return resultado
        if inv_accion2 == 4:  # AJUSTE DE LOTE (+ VERIFICACION)
            cursor.execute(
                "select disponibilidad, unidades \
                 from inv_lotes where id=%s",
                [
                    formulario["codigo_lote"],
                ],
            )
            resultado = cursor.fetchone()
            if (
                resultado["disponibilidad"] < int(formulario["unidades"])
                and int(formulario["tipo_ajuste"]) == 1
            ):
                # EL LOTE NO TIENE SUFICIENTES UNIDADES COMO PARA AJUSTAR
                cursor.close()
                return "NOT-ENOUGH"
            if (
                resultado["disponibilidad"] + int(formulario["unidades"])
                > resultado["unidades"]
                and int(formulario["tipo_ajuste"]) == 2
            ):
                # EL AJUSTE ES MAYOR A LA CAPACIDAD ORIGINAL DEL LOTE
                cursor.close()
                return "TOO-MUCH"
            # SI LA VALIDACION SALE BIEN, SE HACE EL AJUSTE
            if int(formulario["tipo_ajuste"]) == 1:
                unidades_nuevas = resultado["disponibilidad"] - int(
                    formulario["unidades"]
                )
            elif int(formulario["tipo_ajuste"]) == 2:
                unidades_nuevas = resultado["disponibilidad"] + int(
                    formulario["unidades"]
                )
            cursor.execute(
                "update inv_lotes set disponibilidad = %s where id=%s",
                [
                    unidades_nuevas,
                    formulario["codigo_lote"],
                ],
            )
            cursor.execute(
                "insert into inv_lotes_log (id_lote, tipo, unidades, id_usuario, comentario) \
                 values (%s,%s,%s,%s,%s)",
                [
                    formulario["codigo_lote"],
                    formulario["tipo_ajuste"],
                    int(formulario["unidades"]),
                    session["id"],
                    formulario["comentario"],
                ],
            )
            mysql.connection.commit()
            cursor.close()
            return "OK"
        if inv_accion2 == 5:  # CONSULTA DATOS DE UN LOTE
            cursor.execute(
                'SELECT l.id, l.fecha_ingreso, l.factura, monto_factura, precio_venta precio, date_format(fecha_factura,"%%Y-%%m-%%d") fecha_factura \
                    , unidades, l.id_estado estado, disponible, disponibilidad unidades_disponibles, p.nombre proveedor, flete, aduana, username, ubicacion \
                    , ifnull(round(monto_factura/(1-(fm.descuento/fm.monto)),2),monto_factura) monto_factura_sin_descuento, ifnull(round(fm.descuento/fm.monto,6),0) pct_descuento, f_impuestos_incluidos, precio_taller precio_a_taller \
                    FROM inv_lotes l left join proveedores p on p.id=l.id_proveedor \
                    left join kapps_db.accounts a on a.id=l.id_usuario_ingresa \
                        left join inv_factura_maestra fm on fm.factura=l.factura \
                    WHERE l.id=%s',
                [
                    formulario["id_lote"],
                ],
            )
            resultado = cursor.fetchone()
            cursor.close()
            return jsonify(resultado=resultado)
        if inv_accion2 == 6:  # ACTUALIZA DATOS DE UN LOTE
            proveedor=formulario["proveedor"].upper().strip()
            cursor.execute("SELECT id id_proveedor FROM proveedores WHERE nombre = %s", [proveedor])
            datos = cursor.fetchone()
            if datos is None:
                cursor.close()
                return "NO-PROVEEDOR"
            else:
                id_proveedor = datos["id_proveedor"]
                cursor.execute(
                    'UPDATE inv_lotes \
                    set factura=%s, monto_factura=%s, fecha_factura=%s, id_proveedor=%s, precio_venta=%s, flete=%s, aduana=%s \
                        , costo_unitario=%s, ubicacion=%s, f_impuestos_incluidos = %s, precio_taller = %s \
                    where id=%s',[
                        formulario["factura"].upper().strip(),
                        formulario["monto_factura"],
                        formulario["fecha_factura"],
                        id_proveedor,
                        formulario["precio_venta"],
                        formulario["flete"],
                        formulario["aduana"],
                        formulario["costo_unitario"],
                        formulario["ubicacion"],
                        formulario["f_impuestos_incluidos"],
                        formulario["precio_a_taller"],
                        formulario["id_lote"],
                    ],
                )
                mysql.connection.commit()
                cursor.close()
                return "OK"
        if inv_accion2 == 7:  # Consulta Factura 
            proveedor=formulario["proveedor"].upper().strip()
            cursor.execute("SELECT id id_proveedor FROM proveedores WHERE nombre = %s", [proveedor])
            datos = cursor.fetchone()
            if datos is None:
                cursor.close()
                return "NO-PROVEEDOR"
            else:
                id_proveedor = datos["id_proveedor"]
                cursor.execute(
                    'select * from inv_factura_maestra \
                    where factura=%s and id_proveedor=%s',[
                        formulario["factura"].strip(),
                        id_proveedor,
                        ],
                )
                datos = cursor.fetchone()
                cursor.close()
                if datos is None:
                    return "NO-FACTURA"
                else:
                    return jsonify(resultado="OK",datos=datos)
        if inv_accion2 == 8:  # GUARDAR/ACTUALIZAR Factura 
            proveedor=formulario["proveedor"].upper().strip()
            cursor.execute("SELECT id id_proveedor FROM proveedores WHERE nombre = %s", [proveedor])
            datos = cursor.fetchone()
            if datos is None:
                cursor.close()
                return "NO-PROVEEDOR"
            else:
                id_proveedor = datos["id_proveedor"]
                cursor.execute(
                    'select * from inv_factura_maestra \
                    where factura=%s and id_proveedor=%s',[
                        formulario["factura"].strip(),
                        id_proveedor,
                        ],
                )
                datos = cursor.fetchone()
                if datos is None: # LA FACTURA NO EXISTE, SE DEBE INGRESAR
                    cursor.execute(
                    'insert into inv_factura_maestra (factura, id_proveedor, monto, descuento,id_usuario) \
                    values (%s,%s,%s,%s,%s)',[
                        formulario["factura"].strip(),
                        id_proveedor,
                        formulario["monto"],
                        formulario["descuento"],
                        session["id"]
                        ],
                    )
                    mysql.connection.commit()
                    cursor.close()
                    return "FACTURA-INGRESADA"
                else: # LA FACGTURA EXISTE, SE DEBE ACTUALIZAR
                    cursor.execute(
                    'update inv_factura_maestra set monto=%s, descuento=%s, id_usuario_modifica=%s, fecha_modifica=sysdate() \
                    where factura=%s and id_proveedor=%s',[
                        formulario["monto"],
                        formulario["descuento"],
                        session["id"],
                        formulario["factura"].strip(),
                        id_proveedor,
                        ],
                    )
                    mysql.connection.commit()
                    cursor.close()
                    return "FACTURA-ACTUALIZADA"
        if inv_accion2 == 9: # DATOS DE LA ULTIMA FACTURA INGRESADA
            cursor.execute(
                'select l.factura, p.nombre proveedor, ifnull(round(fm.descuento/fm.monto,4),0) pct_descuento \
                from inv_lotes l left join proveedores p on p.id=l.id_proveedor \
	                left join inv_factura_maestra fm on fm.factura=l.factura \
                where l.id=(select max(id) from inv_lotes l2 where l2.id_usuario_ingresa=%s)',
                [session["id"],]
                )
            resultado = cursor.fetchone()
            estado="CERO"
            if cursor.rowcount>0:
                estado="OK"
            cursor.close()
            return jsonify(estado=estado, resultado=resultado)
    return render_template(
        "inventario.html",
        inv_accion=inv_accion,
        inv_accion2=inv_accion2,
        mensaje=mensaje,
        marcas=marcas,
        proveedores=proveedores,
        nuevo_codigo=nuevo_codigo,
        formulario=formulario
    )


def disponibilidad_producto(mysql, codigo_producto):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    unidades_nuevas = 0
    unidades_usadas = 0
    precio_nuevo = 0
    precio_usado = 0
    ubicacion_nuevos = ''
    ubicacion_usados = ''
    precio_nuevo_taller = 0
    precio_usado_taller = 0
    costo_nuevo = 0
    costo_usado = 0
    cursor.execute(
        "select ifnull(sum(case when l.id_estado=1 then disponibilidad else 0 end),0) unidades_nuevas \
                , ifnull(sum(case when l.id_estado=2 then disponibilidad else 0 end),0) unidades_usadas \
                    ,  case when ifnull(sum(case when l.id_estado=1 then disponibilidad else 0 end),0)>0 then \
                (select ubicacion from inv_lotes where codigo_producto=%s and id_estado=1 and disponible=1 and disponibilidad>0 limit 1) else null end ubicacion_nuevos \
                ,  case when ifnull(sum(case when l.id_estado=2 then disponibilidad else 0 end),0)>0 then \
                (select ubicacion from inv_lotes where codigo_producto=%s and id_estado=2 and disponible=1 and disponibilidad>0 limit 1) else null end ubicacion_usados \
             from inv_productos p \
	            left join inv_lotes l on l.codigo_producto=p.id \
            where p.id=%s and p.estado=1 and l.disponibilidad>0 and l.disponible=1",
        [
            codigo_producto,codigo_producto,codigo_producto
        ],
    )
    resultado = cursor.fetchone()
    if resultado["unidades_nuevas"] > 0 or resultado["unidades_usadas"] > 0:
        unidades_nuevas = int(resultado["unidades_nuevas"])
        unidades_usadas = int(resultado["unidades_usadas"])
        ubicacion_nuevos = resultado["ubicacion_nuevos"]
        ubicacion_usados = resultado["ubicacion_usados"]
        # Precio Nuevo
        cursor.execute(
            "select precio_venta, precio_taller, costo_unitario from inv_lotes \
                where id = (select max(id) from inv_lotes \
                            where codigo_producto=%s and id_estado=1 and disponibilidad>0)",
            [
                codigo_producto,
            ],
        )
        resultado = cursor.fetchone()
        if resultado is not None:
            precio_nuevo = resultado["precio_venta"]
            precio_nuevo_taller = resultado["precio_taller"]
            costo_nuevo = resultado["costo_unitario"]
        # Precio Usado
        cursor.execute(
            "select precio_venta, precio_taller, costo_unitario from inv_lotes \
                where id = (select max(id) from inv_lotes \
                            where codigo_producto=%s and id_estado=2 and disponibilidad>0 and disponible=1)",
            [
                codigo_producto,
            ],
        )
        resultado = cursor.fetchone()
        if resultado is not None:
            precio_usado = resultado["precio_venta"]
            precio_usado_taller = resultado["precio_taller"]
            costo_usado = resultado["costo_unitario"]
    cursor.close()
    datos = {
        "unidades_nuevas": unidades_nuevas,
        "unidades_usadas": unidades_usadas,
        "precio_nuevo": precio_nuevo,
        "precio_nuevo_taller": precio_nuevo_taller,
        "precio_usado": precio_usado,
        "precio_usado_taller": precio_usado_taller,
        "costo_nuevo": costo_nuevo,
        "costo_usado": costo_usado,
        "ubicacion_nuevos": ubicacion_nuevos,
        "ubicacion_usados": ubicacion_usados
    }
    return datos
