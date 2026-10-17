from dataclasses import dataclass
from pathlib import Path

from variables import analizar_linea, es_produccion, leer_archivo


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
    encabezado, lineas = leer_archivo(ruta)
    # Detecta un archivo de cadena en el lugar de la gramática, por encabezado o por contenido
    if encabezado and encabezado[0] == "cadena":
        raise ValueError(f"{ruta}: es un archivo de cadena (%cadena); el orden es: gramática y luego cadena")
    if lineas and not any(es_produccion(linea) for _, linea in lineas):
        raise ValueError(f"{ruta}: ninguna línea es una producción; ¿es un archivo de cadena? "
                         "El orden es: gramática y luego cadena")
    elegido = formato if formato != "auto" else (encabezado[1] if encabezado else None)
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
