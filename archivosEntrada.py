from pathlib import Path

# Relegacion de lectura de los encabezados de los txt 
def leer_documento(ruta, tipo_esperado, exigir_tipo=False):
    ruta = Path(ruta)
    if ruta.suffix.lower() != ".txt":
        raise ValueError(f"{ruta}: se esperaba un archivo .txt")
    encabezados = {}
    lineas = []
    with ruta.open(encoding="utf-8-sig") as archivo:
        for numero, linea in enumerate(archivo, start=1):
            linea = linea.strip()
            if not linea:
                continue
            if not linea.startswith("%"):
                lineas.append((numero, linea))
                continue
            partes = linea.split()
            if len(partes) != 2 or partes[0] not in {"%tipo", "%formato", "%cadena"}:
                raise ValueError(f"{ruta}, línea {numero}: encabezado inválido; use %formato o %cadena")
            clave, valor = partes
            if clave in encabezados or lineas:
                raise ValueError(f"{ruta}, línea {numero}: el encabezado debe aparecer una sola vez, antes del contenido")
            permitidos = {"gramatica", "cadena"} if clave == "%tipo" else {"libre", "espacios", "compacto"}
            if valor not in permitidos:
                opciones = ", ".join(sorted(permitidos))
                raise ValueError(f"{ruta}, línea {numero}: {clave} inválido; valores: {opciones}")
            encabezados[clave] = valor
    tipo = encabezados.get("%tipo")
    if "%cadena" in encabezados:
        if tipo == "gramatica" or "%formato" in encabezados:
            raise ValueError(f"{ruta}: %cadena no se combina con %formato ni %tipo gramatica")
        tipo = "cadena"
    elif tipo is None and "%formato" in encabezados:
        tipo = "gramatica"
    if tipo is None and exigir_tipo:
        raise ValueError(f"{ruta}: falta el encabezado %cadena libre o %cadena compacto (también se admite %tipo cadena)")
    if tipo is not None and tipo != tipo_esperado:
        raise ValueError(f"{ruta}: se esperaba %tipo {tipo_esperado}, pero el archivo declara %tipo {tipo}")
    formato = encabezados.get("%cadena", encabezados.get("%formato"))
    return lineas, "espacios" if formato == "libre" else formato


def leer_cadenas(ruta):
    lineas, formato = leer_documento(ruta, "cadena", exigir_tipo=True)
    return lineas or [(None, "")], formato or "espacios"

# Tokenización de cadenas según el formato especificado en los encabezados
def tokenizar_cadena(texto, formato="espacios", minusculas=True):
    texto = texto.casefold() if minusculas else texto
    if formato in {"espacios", "libre"}:
        return tuple(texto.split())
    if formato == "compacto":
        return tuple(texto)
    raise ValueError("formato de cadena inválido; use espacios o compacto")
