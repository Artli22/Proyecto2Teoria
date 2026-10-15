from variables import mostrar_cuerpo

# Diferenciador entre producciones con terminales y no terminales 
def es_unitaria(cuerpo, no_terminales):
    return len(cuerpo) == 1 and cuerpo[0] in no_terminales

# Encontar cierres unarios, diferencia conexiones con producciones terminales
def encontrar_cierres_unitarios(producciones):
    no_terminales = set(producciones)
    adyacencias = {
        variable: {c[0] for c in opciones if es_unitaria(c, no_terminales)}
        for variable, opciones in producciones.items()
    }
    cierres = {}
    for variable in producciones:
        visitados = {variable}
        pendientes = [variable]
        while pendientes:
            actual = pendientes.pop()
            for destino in sorted(adyacencias[actual]):
                if destino not in visitados:
                    visitados.add(destino)
                    pendientes.append(destino)
        cierres[variable] = visitados
    return cierres

# Funciones para eliminar producciones unarias
def eliminar_unitarias(inicio, producciones):
    if inicio not in producciones:
        raise ValueError("el símbolo inicial debe estar en producciones")
    no_terminales = set(producciones)
    cierres = encontrar_cierres_unitarios(producciones)
    resultado = {variable: set() for variable in producciones}
    incorporaciones = []
    for variable in producciones:
        for origen in sorted(cierres[variable]):
            for cuerpo in sorted(producciones[origen]):
                if not es_unitaria(cuerpo, no_terminales):
                    resultado[variable].add(cuerpo)
                    incorporaciones.append((variable, origen, cuerpo))
    return resultado, cierres, incorporaciones

# Imprimir pasos de eliminación de producciones unarias 
def formatear_pasos_unitarias(inicio, resultado, cierres, incorporaciones):
    cierres_texto = [
        f"   {variable}: {{{', '.join(sorted(cierre))}}}"
        for variable, cierre in cierres.items()
    ]

    heredadas_texto = [
        f"   {variable} → {mostrar_cuerpo(cuerpo)} (desde {origen})"
        for variable, origen, cuerpo in incorporaciones
        if variable != origen
    ]

    gramatica_texto = []
    for variable, opciones in resultado.items():
        alternativas = " | ".join(
            mostrar_cuerpo(cuerpo)
            for cuerpo in sorted(opciones)
        )
        gramatica_texto.append(f"   {variable} → {alternativas or '∅'}")

    return "\n".join([
        "\n=== Eliminación de producciones unitarias ===",
        "\n1. Cierres unitarios (incluyen el propio no terminal):",
        *cierres_texto,
        "\n2. Producciones no unitarias heredadas:",
        *(heredadas_texto or ["   Ninguna"]),
        f"\n3. Gramática sin unitarias (inicio: {inicio}):",
        *gramatica_texto,
    ])


def mostrar_pasos_unitarias(inicio, producciones):
    resultado, cierres, incorporaciones = eliminar_unitarias(
        inicio, producciones
    )

    texto = formatear_pasos_unitarias(
        inicio, resultado, cierres, incorporaciones
    )
    print(texto)

    return resultado
