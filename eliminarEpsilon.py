from itertools import product
from variables import EPSILON, mostrar_cuerpo


def encontrar_anulables(producciones):
    """Calcula el cierre de variables que pueden generar ε."""
    anulables = set()
    pasos = []
    while True:
        nuevos = []
        for variable, alternativas in producciones.items():
            if variable in anulables:
                continue
            for cuerpo in sorted(alternativas):
                if not cuerpo or (cuerpo and all(
                    simbolo in anulables for simbolo in cuerpo
                )):
                    nuevos.append((variable, cuerpo))
                    break
        if not nuevos:
            return anulables, pasos
        for variable, cuerpo in nuevos:
            anulables.add(variable)
            pasos.append((variable, cuerpo))


def eliminar_epsilon(inicio, producciones):
    """Devuelve gramática sin ε; preservar ε inicial queda pendiente para fase 1."""
    anulables, pasos = encontrar_anulables(producciones)
    resultado = {variable: set() for variable in producciones}
    combinaciones = []

    for variable, alternativas in producciones.items():
        for cuerpo in sorted(alternativas):
            if not cuerpo:
                continue
            posiciones = [i for i, simbolo in enumerate(cuerpo) if simbolo in anulables]
            casos = []
            for decisiones in product((False, True), repeat=len(posiciones)):
                omitidas = {posicion for posicion, omitir in zip(posiciones, decisiones) if omitir}
                generado = tuple(simbolo for i, simbolo in enumerate(cuerpo) if i not in omitidas)
                if generado and generado not in resultado[variable]:
                    resultado[variable].add(generado)
                casos.append((tuple(i + 1 for i in sorted(omitidas)), generado))
            combinaciones.append((variable, cuerpo, casos))

    return resultado, anulables, pasos, combinaciones


def mostrar_pasos(inicio, producciones):
    resultado, anulables, pasos, combinaciones = eliminar_epsilon(inicio, producciones)
    print("\n1. Variables anulables:")
    for variable, cuerpo in pasos:
        print(f"   {variable} es anulable por {variable} → {mostrar_cuerpo(cuerpo)}")
    if not pasos:
        print("   Ninguna")
    print(f"   Conjunto final: {{{', '.join(sorted(anulables))}}}")

    print("\n2. Combinaciones de símbolos anulables:")
    for variable, cuerpo, casos in combinaciones:
        print(f"   {variable} → {mostrar_cuerpo(cuerpo)}: {len(casos)} caso(s)")
        print("      Posiciones omitidas | Producción generada | Observación")
        print("      --------------------+---------------------+--------------------------")
        for omitidas, generado in casos:
            posiciones = ", ".join(map(str, omitidas)) if omitidas else "Ninguna"
            nota = ""
            if not generado:
                nota = "Se descarta"
            print(f"      {posiciones:<20}| {mostrar_cuerpo(generado):<20}| {nota}")

    print("\n3. Gramática resultante:")
    for variable, alternativas in resultado.items():
        print(f"   {variable} → {' | '.join(mostrar_cuerpo(c) for c in sorted(alternativas)) if alternativas else '∅'}")
    return resultado