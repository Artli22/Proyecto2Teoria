from pathlib import Path

from variables import EPSILON, es_produccion, leer_archivo


# Separa la cadena en símbolos: en espacios cada palabra es un símbolo, en compacto cada carácter.
# Sin encabezado: con espacios se separa por palabras; sin espacios se trata como un solo símbolo
# si es terminal de la gramática (ej. "cooks"), y si no, cada carácter es un símbolo
def separar_simbolos(texto, formato, terminales=frozenset()):
    if formato == "espacios":
        return tuple(texto.split())
    if formato == "compacto":
        if any(c.isspace() for c in texto):
            raise ValueError("la cadena compacta no debe tener espacios; use %cadena espacios")
        return tuple(texto)
    if " " in texto or texto in terminales:
        return tuple(texto.split())
    return tuple(texto)


# Funcion para leer la cadena w; el encabezado %cadena es opcional
def leer_cadena(ruta, terminales=frozenset()):
    ruta = Path(ruta)
    encabezado, lineas = leer_archivo(ruta)
    # Detecta un archivo de gramática en el lugar de la cadena, por encabezado o por contenido
    if encabezado and encabezado[0] == "gramatica":
        raise ValueError(f"{ruta}: es un archivo de gramática (%formato); el orden es: gramática y luego cadena")
    for numero, linea in lineas:
        if es_produccion(linea):
            raise ValueError(f"{ruta}, línea {numero}: parece una producción; ¿es un archivo de gramática? "
                             "El orden es: gramática y luego cadena")
    if len(lineas) > 1:
        raise ValueError(f"{ruta}: el archivo debe contener una sola cadena (se encontraron {len(lineas)} líneas)")
    texto = lineas[0][1] if lineas else ""
    if not texto or texto == EPSILON:
        return ()
    try:
        return separar_simbolos(texto, encabezado[1] if encabezado else "auto", terminales)
    except ValueError as error:
        raise ValueError(f"{ruta}, línea {lineas[0][0]}: {error}") from error


# Una cadena sin ningún terminal de la gramática indica que se cruzaron los archivos
def validar_cadena(w, gramatica):
    desconocidos = sorted(set(w) - gramatica.terminales)
    if w and len(desconocidos) == len(set(w)):
        raise ValueError("ningún símbolo de la cadena es terminal de la gramática; "
                         "revise que los archivos correspondan entre sí")
    return desconocidos
