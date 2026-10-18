from dataclasses import dataclass
from pathlib import Path

from variables import analizar_linea
from archivosEntrada import leer_documento


@dataclass
class Gramatica:
    inicio: str
    no_terminales: set[str]
    terminales: set[str]
    producciones: dict[str, set[tuple[str, ...]]]


def _interpretar(ruta, lineas, formato):
    """Valida una interpretación completa, incluidos los símbolos declarados."""
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


def leer_gramatica(ruta, formato="auto"):
    """Usa encabezado o detecta ambas interpretaciones sin adivinar ambigüedades.

    Un formato explícito tiene prioridad sobre %formato. Los encabezados
    %tipo y %formato deben ser únicos y preceder a las producciones.
    """
    if formato == "libre":
        formato = "espacios"
    if formato not in {"auto", "espacios", "compacto"}:
        raise ValueError("formato desconocido; use auto, espacios o compacto")
    ruta = Path(ruta)
    lineas, encabezado = leer_documento(ruta, "gramatica")
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

