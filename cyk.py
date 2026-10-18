from dataclasses import dataclass
from time import perf_counter

from formaChomsky import es_forma_chomsky


@dataclass(frozen=True)
class ReferenciaCYK:
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
    return tuple((texto.casefold() if minusculas else texto).split())

# Indexación rápida de la gramática para CYK: léxicos y binarias.
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

# Reconstrucción del árbol de derivación a partir de la tabla CYK.
def _construir_arbol(inicio, tokens, tabla):
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

# Ejecución del algoritmo CYK sobre la secuencia de tokens y la gramática en Chomsky.
def ejecutar_cyk(inicio, producciones, tokens):
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
    """Dibuja ramas conservando el orden de los hijos, sin recursión."""
    if arbol is None:
        return "   No hay árbol: la entrada no pertenece al lenguaje."
    lineas = ["   " + arbol.simbolo]
    pendientes = [
        (hijo, "", i == len(arbol.hijos) - 1)
        for i, hijo in reversed(list(enumerate(arbol.hijos)))
    ]
    while pendientes:
        nodo, prefijo, ultimo = pendientes.pop()
        rama = "└── " if ultimo else "├── "
        lineas.append("   " + prefijo + rama + nodo.simbolo)
        prefijo_hijos = prefijo + ("    " if ultimo else "│   ")
        pendientes.extend(
            (hijo, prefijo_hijos, i == len(nodo.hijos) - 1)
            for i, hijo in reversed(list(enumerate(nodo.hijos)))
        )
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

# Recopilar los pasos y resultados del análisis CYK en terminal 
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
