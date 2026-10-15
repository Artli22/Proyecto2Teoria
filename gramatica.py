from dataclasses import dataclass
from pathlib import Path

from variables import analizar_linea


@dataclass
class Gramatica:
    inicio: str
    no_terminales: set[str]
    terminales: set[str]
    producciones: dict[str, set[tuple[str, ...]]]


# Función interna para interpretar la gramática a partir de las líneas del archivo 
def _interpretar(ruta, lineas, formato):
    producciones = {}
    for numero, linea in lineas:
        try:
            variable, alternativas = analizar_linea(linea, formato)
        except ValueError as error:
            raise ValueError(f"{ruta}, línea {numero}: {error}") from error
        producciones.setdefault(variable, set()).update(alternativas)
    if not producciones:
        raise ValueError(f"{ruta}: el archivo está vacío")
    no_terminales = set(producciones)
    usados = {s for opciones in producciones.values() for cuerpo in opciones for s in cuerpo}
    faltantes = {s for s in usados if s[0].isupper()} - no_terminales
    if faltantes:
        raise ValueError(f"{ruta}: variables sin producción: {', '.join(sorted(faltantes))}")
    return Gramatica(next(iter(producciones)), no_terminales, usados - no_terminales, producciones)

# Funcion para leer la gramatica 
def leer_gramatica(ruta, formato="auto"):
    # Funcion de encabezados para evitar ambigüedades 
    if formato not in {"auto", "espacios", "compacto"}:
        raise ValueError("formato desconocido; use auto, espacios o compacto")
    ruta = Path(ruta)
    lineas = []
    encabezado = None
    with ruta.open(encoding="utf-8-sig") as archivo:
        for numero, linea in enumerate(archivo, start=1):
            linea = linea.strip()
            if not linea:
                continue
            if linea.startswith("%"):
                partes = linea.split()
                if len(partes) != 2 or partes[0] != "%formato" or partes[1] not in {"espacios", "compacto"}:
                    raise ValueError(f"{ruta}, línea {numero}: use %formato espacios o %formato compacto")
                if encabezado is not None or lineas:
                    raise ValueError(f"{ruta}, línea {numero}: el encabezado debe aparecer una sola vez, antes de las producciones")
                encabezado = partes[1]
            else:
                lineas.append((numero, linea))
    elegido = formato if formato != "auto" else encabezado
    if elegido is not None:
        return _interpretar(ruta, lineas, elegido)
    resultados = []
    errores = []
    for candidato in ("espacios", "compacto"):
        try:
            resultados.append(_interpretar(ruta, lineas, candidato))
        except ValueError as error:
            errores.append(f"{candidato}: {error}")
    if not resultados:
        raise ValueError("No se pudo leer la gramática.\n" + "\n".join(errores))
    if len(resultados) == 1 or resultados[0] == resultados[1]:
        return resultados[0]
    raise ValueError(f"{ruta}: formato ambiguo; agregue %formato espacios o %formato compacto al inicio del archivo")
