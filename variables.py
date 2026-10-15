import re

EPSILON = "ε"
ENCABEZADO = re.compile(r"\s*([A-Z][A-Za-z0-9_]*)\s*(?:→|->|::=)\s*(.*?)\s*")


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