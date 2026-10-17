from dataclasses import dataclass
from time import perf_counter

from formaChomsky import es_forma_chomsky


@dataclass(frozen=True)
class ReferenciaCYK:
    """Una derivación por no terminal y celda: terminal o pareja con corte."""
    terminal: str | None = None
    corte: int | None = None
    izquierda: str | None = None
    derecha: str | None = None


@dataclass(frozen=True)
class NodoArbol:
    simbolo: str
    hijos: tuple["NodoArbol", ...] = ()


@dataclass
class ResultadoCYK:
    inicio: str
    tokens: tuple[str, ...]
    aceptada: bool
    tiempo_segundos: float
    tabla: dict[tuple[int, int], dict[str, ReferenciaCYK]]
    arbol: NodoArbol | None


def tokenizar_frase(texto, minusculas=True):
    """Un token por palabra separada por espacios; no elimina puntuación.

    La conversión a minúsculas es una política de entrada, no parte de CYK.
    ejecutar_cyk() recibe los tokens exactos y no los normaliza.
    """
    return tuple((texto.casefold() if minusculas else texto).split())


def _indexar_gramatica(inicio, producciones):
    if not es_forma_chomsky(inicio, producciones):
        raise ValueError("CYK requiere un inicio declarado y reglas A → terminal o A → B C, sin ε ni unitarias")
    lexicales = {}
    binarias = {}
    for variable in sorted(producciones):
        for cuerpo in sorted(producciones[variable]):
            indice = lexicales if len(cuerpo) == 1 else binarias
            clave = cuerpo[0] if len(cuerpo) == 1 else cuerpo
            indice.setdefault(clave, []).append(variable)
    return lexicales, binarias


def _construir_arbol(inicio, tokens, tabla):
    """Reconstruye una derivación con las referencias, sin llamadas recursivas."""
    raiz = (0, len(tokens), inicio)
    nodos = {}
    pendientes = [(raiz, False)]
    while pendientes:
        clave, visitado = pendientes.pop()
        if clave in nodos:
            continue
        i, j, variable = clave
        referencia = tabla[i, j][variable]
        if referencia.terminal is not None:
            nodos[clave] = NodoArbol(variable, (NodoArbol(referencia.terminal),))
            continue
        izquierda = (i, referencia.corte, referencia.izquierda)
        derecha = (referencia.corte, j, referencia.derecha)
        if visitado:
            nodos[clave] = NodoArbol(variable, (nodos[izquierda], nodos[derecha]))
        else:
            pendientes.extend([(clave, True), (derecha, False), (izquierda, False)])
    return nodos[raiz]


def ejecutar_cyk(inicio, producciones, tokens):
    """CYK sobre tokens exactos y gramática en Chomsky, con una derivación.

    tabla[i, j] guarda los no terminales que producen tokens[i:j], con j
    exclusivo. Se calculan longitudes crecientes y todos sus posibles cortes.
    Se rechaza la entrada vacía, conforme a la eliminación total de ε.

    El tiempo incluye construir/llenar la tabla y decidir pertenencia. Excluye
    tokenización, validación/indexación de reglas, simplificación, árbol e I/O.
    No modifica la gramática ni la secuencia de entrada.
    """
    if isinstance(tokens, str):
        raise TypeError("pase una secuencia de tokens; para una frase use tokenizar_frase()")
    tokens = tuple(tokens)
    if any(not isinstance(t, str) or not t for t in tokens):
        raise ValueError("cada token debe ser una cadena no vacía")
    lexicales, binarias = _indexar_gramatica(inicio, producciones)

    comienzo = perf_counter()
    n = len(tokens)
    tabla = {(i, j): {} for i in range(n) for j in range(i + 1, n + 1)}
    for i, token in enumerate(tokens):
        for variable in lexicales.get(token, ()):
            tabla[i, i + 1][variable] = ReferenciaCYK(terminal=token)

    for longitud in range(2, n + 1):
        for i in range(n - longitud + 1):
            j = i + longitud
            celda = tabla[i, j]
            for corte in range(i + 1, j):
                for izquierda in sorted(tabla[i, corte]):
                    for derecha in sorted(tabla[corte, j]):
                        for variable in binarias.get((izquierda, derecha), ()):
                            if variable not in celda:
                                celda[variable] = ReferenciaCYK(
                                    corte=corte, izquierda=izquierda, derecha=derecha,
                                )

    aceptada = n > 0 and inicio in tabla[0, n]
    tiempo = perf_counter() - comienzo
    arbol = _construir_arbol(inicio, tokens, tabla) if aceptada else None
    return ResultadoCYK(inicio, tokens, aceptada, tiempo, tabla, arbol)


def formatear_arbol(arbol):
    if arbol is None:
        return "   No hay árbol: la entrada no pertenece al lenguaje."
    lineas = []
    pendientes = [(arbol, 0)]
    while pendientes:
        nodo, profundidad = pendientes.pop()
        lineas.append("   " + "  " * profundidad + nodo.simbolo)
        pendientes.extend((hijo, profundidad + 1) for hijo in reversed(nodo.hijos))
    return "\n".join(lineas)


def formatear_tabla(resultado):
    lineas = ["\nTabla CYK: [i, j) corresponde a tokens[i:j]"]
    if not resultado.tokens:
        lineas.append("   Vacía: no hay tokens.")
    for longitud in range(1, len(resultado.tokens) + 1):
        for i in range(len(resultado.tokens) - longitud + 1):
            j = i + longitud
            variables = ", ".join(sorted(resultado.tabla[i, j]))
            fragmento = " ".join(resultado.tokens[i:j])
            lineas.append(f"   [{i}, {j}) {fragmento!r}: {{{variables}}}")
    return "\n".join(lineas)


def formatear_resultado_cyk(resultado, mostrar_tabla=False):
    frase = " ".join(resultado.tokens) or "(vacía)"
    lineas = [
        "\n=== Resultado CYK ===",
        f"Frase analizada: {frase}",
        f"Pertenece al lenguaje: {'SÍ' if resultado.aceptada else 'NO'}",
        f"Tiempo CYK (tabla y decisión): {resultado.tiempo_segundos * 1000:.6f} ms",
        "\nÁrbol de análisis (gramática en Chomsky):",
        formatear_arbol(resultado.arbol),
    ]
    if mostrar_tabla:
        lineas.append(formatear_tabla(resultado))
    return "\n".join(lineas)
