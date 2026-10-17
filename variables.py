import re

EPSILON = "ε"
ENCABEZADO = re.compile(r"\s*([A-Z][A-Za-z0-9_]*)\s*(?:→|->|::=)\s*(.*?)\s*")
# Indicadores de archivo: el primero marca una gramática y el segundo una cadena w
TIPOS_ARCHIVO = {"%formato": "gramatica", "%cadena": "cadena"}


def es_produccion(linea):
    return ENCABEZADO.fullmatch(linea) is not None


def leer_archivo(ruta):
    """Devuelve (tipo, formato) del encabezado % (o None) y las líneas no vacías numeradas."""
    encabezado = None
    lineas = []
    with open(ruta, encoding="utf-8-sig") as archivo:
        for numero, linea in enumerate(archivo, start=1):
            linea = linea.strip()
            if not linea:
                continue
            if linea.startswith("%"):
                partes = linea.split()
                if len(partes) != 2 or partes[0] not in TIPOS_ARCHIVO or partes[1] not in {"espacios", "compacto"}:
                    raise ValueError(f"{ruta}, línea {numero}: use %formato espacios|compacto (gramática) "
                                     "o %cadena espacios|compacto (cadena)")
                if encabezado is not None or lineas:
                    raise ValueError(f"{ruta}, línea {numero}: el encabezado debe aparecer una sola vez, antes del contenido")
                encabezado = (TIPOS_ARCHIVO[partes[0]], partes[1])
            else:
                lineas.append((numero, linea))
    return encabezado, lineas


def analizar_linea(linea, formato="espacios"):
    """Lee símbolos explícitos. En modo compacto cada carácter es un símbolo."""
    if formato not in {"espacios", "compacto"}:
        raise ValueError("formato desconocido; use espacios o compacto")
    coincidencia = ENCABEZADO.fullmatch(linea)
    if not coincidencia:
        raise ValueError("se esperaba un no terminal seguido de →, -> o ::=")
    variable, cuerpo = coincidencia.groups()
    if formato == "compacto" and len(variable) != 1:
        raise ValueError("el formato compacto requiere variables de una letra")
    alternativas = set()
    for parte in cuerpo.split("|"):
        parte = parte.strip()
        if not parte:
            raise ValueError("hay una alternativa vacía; escriba ε explícitamente")
        if parte == EPSILON:
            alternativas.add(())
            continue
        if EPSILON in parte:
            raise ValueError("ε debe aparecer como alternativa completa")
        if formato == "compacto":
            if not re.fullmatch(r"(?:[A-Za-z0-9]|//)+", parte):
                raise ValueError("cuerpo compacto inválido; no use espacios")
            simbolos = tuple(parte.replace("//", "/"))
        else:
            simbolos = tuple(parte.split())
            if any(not re.fullmatch(r"[A-Za-z0-9_]+|[^\w\s|ε]", s) for s in simbolos):
                raise ValueError(f"símbolo inválido en {parte!r}")
        alternativas.add(simbolos)
    return variable, alternativas


def mostrar_cuerpo(cuerpo):
    return " ".join(cuerpo) if cuerpo else EPSILON