from pathlib import Path
from variables import analizar_linea


def leer_gramatica(ruta):
    """Lee una producción por línea; combina líneas del mismo no terminal."""
    ruta = Path(ruta)
    producciones = {}
    with ruta.open(encoding="utf-8-sig") as archivo:
        for numero, linea in enumerate(archivo, start=1):
            if not linea.strip():
                raise ValueError(f"{ruta}, línea {numero}: línea vacía")
            try:
                variable, alternativas = analizar_linea(linea.rstrip("\r\n"))
            except ValueError as error:
                raise ValueError(f"{ruta}, línea {numero}: {error}") from error
            producciones.setdefault(variable, [])
            for alternativa in alternativas:
                if alternativa not in producciones[variable]:
                    producciones[variable].append(alternativa)
    if not producciones:
        raise ValueError(f"{ruta}: el archivo está vacío")
    inicio = next(iter(producciones))
    faltantes = {simbolo for opciones in producciones.values() for opcion in opciones
                 for simbolo in opcion if simbolo.isupper()} - producciones.keys()
    if faltantes:
        raise ValueError(f"{ruta}: variables sin producción: {', '.join(sorted(faltantes))}")
    return inicio, producciones
