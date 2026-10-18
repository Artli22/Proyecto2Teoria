from itertools import product

from variables import mostrar_cuerpo

# Funcion para eliminar producciones ε 
def encontrar_anulables(producciones):
    anulables = set()
    pasos = []

    while True:
        nuevos = []

        for variable, alternativas in producciones.items():
            if variable in anulables:
                continue

            for cuerpo in sorted(alternativas):
                # all() también devuelve True para (), que representa ε.
                if all(simbolo in anulables for simbolo in cuerpo):
                    nuevos.append((variable, cuerpo))
                    break

        if not nuevos:
            return anulables, pasos

        for variable, cuerpo in nuevos:
            anulables.add(variable)
            pasos.append((variable, cuerpo))

# Conserva el lenguaje original, con excepcion a la cadena vacia acorde a la metodologia mostrada en clase 
def eliminar_epsilon(inicio, producciones):
    anulables, pasos = encontrar_anulables(producciones)
    resultado = {variable: set() for variable in producciones}
    combinaciones = []

    for variable, alternativas in producciones.items():
        for cuerpo in sorted(alternativas):
            if not cuerpo:
                continue

            posiciones = [
                i
                for i, simbolo in enumerate(cuerpo)
                if simbolo in anulables
            ]

            casos = []

            for decisiones in product(
                (False, True),
                repeat=len(posiciones),
            ):
                omitidas = {
                    posicion
                    for posicion, omitir in zip(posiciones, decisiones)
                    if omitir
                }

                generado = tuple(
                    simbolo
                    for i, simbolo in enumerate(cuerpo)
                    if i not in omitidas
                )

                # Se descarta ε incluso si la variable es el inicio.
                if generado:
                    resultado[variable].add(generado)

                casos.append((
                    tuple(i + 1 for i in sorted(omitidas)),
                    generado,
                ))

            combinaciones.append((variable, cuerpo, casos))

    return resultado, anulables, pasos, combinaciones

# Resultados impresos en terminal 
def mostrar_pasos(inicio, producciones):
    resultado, anulables, pasos, combinaciones = eliminar_epsilon(
        inicio,
        producciones,
    )

    print("\n1. Variables anulables:")

    for variable, cuerpo in pasos:
        print(
            f"   {variable} es anulable por "
            f"{variable} → {mostrar_cuerpo(cuerpo)}"
        )

    if not pasos:
        print("   Ninguna")

    print(f"   Conjunto final: {{{', '.join(sorted(anulables))}}}")

    print("\n2. Combinaciones de símbolos anulables:")

    for variable, cuerpo, casos in combinaciones:
        print(
            f"   {variable} → {mostrar_cuerpo(cuerpo)}: "
            f"{len(casos)} caso(s)"
        )
        print("      Posiciones omitidas | Producción generada")
        print("      --------------------+---------------------")

        for omitidas, generado in casos:
            posiciones = (
                ", ".join(map(str, omitidas))
                if omitidas
                else "Ninguna"
            )

            nota = "Se descarta ε" if not generado else ""

            print(f"      {posiciones:<20}| {mostrar_cuerpo(generado)}")

    print(f"\n3. Gramática resultante (inicio: {inicio}):")

    for variable, alternativas in resultado.items():
        texto = " | ".join(
            mostrar_cuerpo(cuerpo)
            for cuerpo in sorted(alternativas)
        )
        print(f"   {variable} → {texto or '∅'}")

    return resultado
