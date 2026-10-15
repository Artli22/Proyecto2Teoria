from itertools import product
from variables import EPSILON


def encontrar_anulables(producciones):
    """Calcula el cierre de variables que pueden generar ε."""
    anulables = set()
    pasos = []
    while True:
        nuevos = []
        for variable, alternativas in producciones.items():
            if variable in anulables:
                continue
            for cuerpo in alternativas:
                if cuerpo == EPSILON or (cuerpo and all(
                    simbolo.isupper() and simbolo in anulables for simbolo in cuerpo
                )):
                    nuevos.append((variable, cuerpo))
                    break
        if not nuevos:
            return anulables, pasos
        for variable, cuerpo in nuevos:
            anulables.add(variable)
            pasos.append((variable, cuerpo))


def eliminar_epsilon(inicio, producciones):
    """Devuelve gramática sin ε y detalle de las 2^m combinaciones."""
    anulables, pasos = encontrar_anulables(producciones)
    resultado = {variable: [] for variable in producciones}
    combinaciones = []

    for variable, alternativas in producciones.items():
        for cuerpo in alternativas:
            if cuerpo == EPSILON:
                continue
            posiciones = [i for i, simbolo in enumerate(cuerpo) if simbolo in anulables]
            casos = []
            for decisiones in product((False, True), repeat=len(posiciones)):
                omitidas = {posicion for posicion, omitir in zip(posiciones, decisiones) if omitir}
                generado = "".join(simbolo for i, simbolo in enumerate(cuerpo) if i not in omitidas)
                if generado and generado not in resultado[variable]:
                    resultado[variable].append(generado)
                casos.append((tuple(i + 1 for i in sorted(omitidas)), generado or EPSILON))
            combinaciones.append((variable, cuerpo, casos))

    return resultado, anulables, pasos, combinaciones


def mostrar_pasos(inicio, producciones):
    resultado, anulables, pasos, combinaciones = eliminar_epsilon(inicio, producciones)
    print("\n1. Variables anulables:")
    for variable, cuerpo in pasos:
        print(f"   {variable} es anulable por {variable} → {cuerpo}")
    if not pasos:
        print("   Ninguna")
    print(f"   Conjunto final: {{{', '.join(sorted(anulables))}}}")

    print("\n2. Combinaciones de símbolos anulables:")
    for variable, cuerpo, casos in combinaciones:
        print(f"   {variable} → {cuerpo}: {len(casos)} caso(s)")
        print("      Posiciones omitidas | Producción generada | Observación")
        print("      --------------------+---------------------+--------------------------")
        for omitidas, generado in casos:
            posiciones = ", ".join(map(str, omitidas)) if omitidas else "Ninguna"
            nota = ""
            if generado == EPSILON:
                nota = "Se descarta"
            print(f"      {posiciones:<20}| {generado:<20}| {nota}")

    print("\n3. Gramática resultante:")
    for variable, alternativas in resultado.items():
        print(f"   {variable} → {' | '.join(alternativas) if alternativas else '∅'}")
    return resultado
