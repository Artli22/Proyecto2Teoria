
import re

EPSILON = "ε"
ENCABEZADO = re.compile(r"\s*([A-Z])\s*(?:→|->|::=)\s*(.*?)\s*")
CUERPO = re.compile(r"(?:[A-Za-z0-9]|//)+")


def analizar_linea(linea):
    """Valida una línea y devuelve su variable y alternativas normalizadas."""
    coincidencia = ENCABEZADO.fullmatch(linea)
    if not coincidencia:
        raise ValueError("se esperaba una variable mayúscula seguida de →, -> o ::=")

    variable, cuerpo = coincidencia.groups()
    alternativas = [parte.strip() for parte in cuerpo.split("|")]
    if any(not parte for parte in alternativas):
        raise ValueError("hay una alternativa vacía; escriba ε explícitamente")

    for parte in alternativas:
        if parte != EPSILON and not CUERPO.fullmatch(parte):
            raise ValueError(f"alternativa inválida: {parte!r}")

    return variable, [parte.replace("//", "/") for parte in alternativas]
