import csv
import json
import urllib.parse
from io import StringIO
from datetime import datetime, timezone

import boto3

s3 = boto3.client("s3")


def lambda_handler(event, context):
    print("=== Lambda activada por evento S3 ===")
    print("Evento recibido:")
    print(json.dumps(event, indent=2))

    records = event.get("Records", [])

    if not records:
        print("No se recibieron registros de S3")
        return {
            "statusCode": 400,
            "body": "No se recibieron registros de S3"
        }

    for record in records:
        bucket = record["s3"]["bucket"]["name"]
        key = record["s3"]["object"]["key"]
        key = urllib.parse.unquote_plus(key)

        print(f"Bucket: {bucket}")
        print(f"Archivo: {key}")

        # 1. Leer el archivo CSV desde S3
        respuesta = s3.get_object(Bucket=bucket, Key=key)
        contenido = respuesta["Body"].read().decode("utf-8-sig")

        # 2. Procesar el CSV
        lector = csv.DictReader(StringIO(contenido))

        registros_procesados = []
        registros_descartados = []
        total_registros = 0

        for fila in lector:
            total_registros += 1
            resultado = procesar_registro(fila)

            if resultado["valido"]:
                registros_procesados.append(resultado["data"])
            else:
                fila["MOTIVO_RECHAZO"] = resultado["error"]
                registros_descartados.append(fila)

        print(f"Total registros: {total_registros}")
        print(f"Registros procesados: {len(registros_procesados)}")
        print(f"Registros descartados: {len(registros_descartados)}")

        # 3. Guardar CSV de salida (registros procesados)
        if registros_procesados:
            nombre_archivo = key.split("/")[-1].replace(".csv", "_procesados.csv")
            salida_key = f"salida/{nombre_archivo}"
            guardar_csv_s3(registros_procesados, bucket, salida_key)
            print(f"Archivo salida guardado: {salida_key}")

        # 4. Guardar CSV de descartados
        if registros_descartados:
            nombre_archivo = key.split("/")[-1].replace(".csv", "_descartados.csv")
            descartados_key = f"descartados/{nombre_archivo}"
            guardar_csv_s3(registros_descartados, bucket, descartados_key)
            print(f"Archivo descartados guardado: {descartados_key}")

        # 5. Crear resumen del procesamiento
        resumen = {
            "archivo_origen": key,
            "total_registros": total_registros,
            "registros_procesados": len(registros_procesados),
            "registros_descartados": len(registros_descartados),
            "tasa_exito": f"{(len(registros_procesados)/total_registros*100):.2f}%" if total_registros > 0 else "0%",
            "procesado_en_utc": datetime.now(timezone.utc).isoformat(),
            "archivos_generados": {
                "salida": salida_key if registros_procesados else None,
                "descartados": descartados_key if registros_descartados else None
            }
        }

        # 6. Guardar resumen en S3
        nombre_resumen = key.split("/")[-1].replace(".csv", "_resumen.json")
        resumen_key = f"logs/{nombre_resumen}"

        s3.put_object(
            Bucket=bucket,
            Key=resumen_key,
            Body=json.dumps(resumen, ensure_ascii=False, indent=2).encode("utf-8"),
            ContentType="application/json"
        )

        print(f"Resumen guardado: {resumen_key}")
        print("=== Proceso completado exitosamente ===")
        print(json.dumps(resumen, ensure_ascii=False, indent=2))

    return {
        "statusCode": 200,
        "body": json.dumps({
            "mensaje": "Procesamiento completado",
            "registros_procesados": len(registros_procesados),
            "registros_descartados": len(registros_descartados)
        }, ensure_ascii=False)
    }


def procesar_registro(fila):
    """Procesa y valida un registro individual"""

    try:
        # 1. Validar ID
        idcliente = fila.get("IDCLIENTE", "").strip()
        if not idcliente:
            return {"valido": False, "error": "ID_VACIO"}

        # 2. Validar y normalizar RUT
        rut = fila.get("RUT", "").strip()
        if not rut:
            return {"valido": False, "error": "RUT_VACIO"}

        rut_normalizado = normalizar_rut(rut)
        if not rut_normalizado:
            return {"valido": False, "error": "RUT_INVALIDO"}

        # 3. Procesar nombre (separar por comas si es necesario)
        nombre = fila.get("NOMBRE", "").strip()
        apellido_paterno = fila.get("APELLIDOPATERNO", "").strip()
        apellido_materno = fila.get("APELLIDOMATERNO", "").strip()

        if "," in nombre:
            partes = [p.strip() for p in nombre.split(",")]
            nombre = partes[0] if len(partes) > 0 else nombre
            if len(partes) > 1 and not apellido_paterno:
                apellido_paterno = partes[1]
            if len(partes) > 2 and not apellido_materno:
                apellido_materno = partes[2]

        # 4. Normalizar fecha
        fecha = fila.get("FECHAREGISTRO", "").strip()
        fecha_normalizada = normalizar_fecha(fecha)
        if not fecha_normalizada:
            return {"valido": False, "error": "FECHA_INVALIDA"}

        # 5. Campos opcionales
        telefono = fila.get("TELEFONO", "").strip() or "No disponible"
        email = fila.get("EMAIL", "").strip() or "No disponible"
        direccion = fila.get("DIRECCION", "").strip() or "No disponible"
        ciudad = fila.get("CIUDAD", "").strip() or "No disponible"
        codigopostal = fila.get("CODIGOPOSTAL", "").strip() or "No disponible"

        # 6. Pseudonimizar datos sensibles
        rut_pseudonimizado = pseudonimizar_campo(rut_normalizado)
        telefono_pseudonimizado = pseudonimizar_campo(telefono) if telefono != "No disponible" else telefono
        email_pseudonimizado = pseudonimizar_email(email) if email != "No disponible" else email
        direccion_pseudonimizada = pseudonimizar_campo(direccion) if direccion != "No disponible" else direccion
        apellido_paterno_pseudonimizado = pseudonimizar_campo(apellido_paterno) if apellido_paterno else "No disponible"

        registro_procesado = {
            "IDCLIENTE": idcliente,
            "RUT": rut_pseudonimizado,
            "NOMBRE": nombre,
            "APELLIDOPATERNO": apellido_paterno_pseudonimizado,
            "APELLIDOMATERNO": apellido_materno or "No disponible",
            "TELEFONO": telefono_pseudonimizado,
            "EMAIL": email_pseudonimizado,
            "DIRECCION": direccion_pseudonimizada,
            "CIUDAD": ciudad,
            "CODIGOPOSTAL": codigopostal,
            "FECHAREGISTRO": fecha_normalizada
        }

        return {"valido": True, "data": registro_procesado}

    except Exception as e:
        return {"valido": False, "error": f"ERROR: {str(e)}"}


def normalizar_rut(rut):
    """Normaliza RUT a formato XX.XXX.XXX-X"""

    if not rut:
        return None

    rut = rut.replace(".", "").replace("-", "").strip().upper()

    if len(rut) < 8:
        return None

    rut_num = rut[:-1]
    dv = rut[-1]

    if not rut_num.isdigit():
        return None

    rut_num = rut_num.zfill(8)[-8:]
    return f"{rut_num[0:2]}.{rut_num[2:5]}.{rut_num[5:8]}-{dv}"


def normalizar_fecha(fecha_str):
    """Normaliza fecha a formato YYYY-MM-DD"""

    if not fecha_str:
        return None

    fecha_str = fecha_str.strip()

    formatos = [
        "%Y-%m-%d",
        "%d-%m-%Y",
        "%d/%m/%Y",
        "%Y/%m/%d",
        "%d-%m-%y",
        "%d/%m/%y",
        "%Y%m%d"
    ]

    for fmt in formatos:
        try:
            fecha = datetime.strptime(fecha_str, fmt)
            return fecha.strftime("%Y-%m-%d")
        except:
            continue

    return None


def pseudonimizar_campo(campo):
    """Pseudonimiza un campo (oculta últimos 3 caracteres)"""

    if not campo or campo == "No disponible":
        return campo

    campo = str(campo).strip()
    if len(campo) <= 3:
        return "***"

    return campo[:-3] + "***"


def pseudonimizar_email(email):
    """Pseudonimiza email manteniendo dominio"""

    if not email or email == "No disponible":
        return email

    email = email.strip()

    if "@" not in email:
        return "No disponible"

    usuario, dominio = email.split("@", 1)

    if len(usuario) <= 3:
        usuario_oculto = "***"
    else:
        usuario_oculto = usuario[:-3] + "***"

    return f"{usuario_oculto}@{dominio}"


def guardar_csv_s3(registros, bucket, key):
    """Guarda lista de registros como CSV en S3"""

    if not registros:
        return

    output = StringIO()
    fieldnames = registros[0].keys()
    writer = csv.DictWriter(output, fieldnames=fieldnames)

    writer.writeheader()
    writer.writerows(registros)

    s3.put_object(
        Bucket=bucket,
        Key=key,
        Body=output.getvalue().encode("utf-8-sig"),
        ContentType="text/csv"
    )
