from variables import mostrar_cuerpo

# Verificacion de los simbolos de produccion que realmente genera alguna cadena de terminales
def encontrar_generadores(producciones):
    no_terminales = set(producciones)
    generadores = set()
    pasos = []
    while True:
        nuevos = []
        for variable, alternativas in producciones.items():
            if variable in generadores:
                continue
            for cuerpo in sorted(alternativas):
                if all(s not in no_terminales or s in generadores for s in cuerpo):
                    nuevos.append((variable, cuerpo))
                    break
        if not nuevos:
            return generadores, pasos
        for variable, cuerpo in nuevos:
            generadores.add(variable)
            pasos.append((variable, cuerpo))

# Eliminacion de simbolos de produccion que no sean generadores 
def eliminar_no_generadores(inicio, producciones):
    if inicio not in producciones:
        raise ValueError("el símbolo inicial debe estar en producciones")
    generadores, pasos = encontrar_generadores(producciones)
    if inicio not in generadores:
        return {inicio: set()}, generadores, pasos
    no_generadores = set(producciones) - generadores
    resultado = {
        variable: {c for c in opciones if not any(s in no_generadores for s in c)}
        for variable, opciones in producciones.items() if variable in generadores
    }
    return resultado, generadores, pasos

# Verificacion de los simbolos de produccion si puedan alcanzarse 
def encontrar_alcanzables(inicio, producciones):
    if inicio not in producciones:
        raise ValueError("el símbolo inicial debe estar en producciones")
    no_terminales = set(producciones)
    alcanzables = {inicio}
    pendientes = [inicio]
    while pendientes:
        variable = pendientes.pop()
        for cuerpo in sorted(producciones[variable]):
            for simbolo in cuerpo:
                if simbolo in no_terminales and simbolo not in alcanzables:
                    alcanzables.add(simbolo)
                    pendientes.append(simbolo)
    return alcanzables

# Eliminacion de simbolos de produccion que no sean alcanzables 
def eliminar_inalcanzables(inicio, producciones):
    alcanzables = encontrar_alcanzables(inicio, producciones)
    resultado = {
        variable: set(opciones)
        for variable, opciones in producciones.items() if variable in alcanzables
    }
    return resultado, alcanzables

# Resultado de la eliminación de símbolos no generadores e inalcanzables
def eliminar_inutiles(inicio, producciones):
    productiva, generadores, pasos = eliminar_no_generadores(inicio, producciones)
    resultado, alcanzables = eliminar_inalcanzables(inicio, productiva)
    return resultado, generadores, alcanzables, pasos

# Recopilacion de pasos necesarios para asegurar la eliminación de símbolos inútiles
def formatear_pasos_inutiles(inicio, producciones, resultado, generadores, alcanzables, pasos):
    no_generadores = set(producciones) - generadores
    inalcanzables = generadores - alcanzables
    conjunto = lambda simbolos: "{" + ", ".join(sorted(simbolos)) + "}"
    razones = [f"   {v} es generador por {v} → {mostrar_cuerpo(c)}" for v, c in pasos]
    gramatica = []
    for variable, opciones in resultado.items():
        texto = " | ".join(mostrar_cuerpo(c) for c in sorted(opciones))
        gramatica.append(f"   {variable} → {texto or '∅'}")
    aviso = []
    if inicio not in generadores:
        aviso = [f"   Lenguaje vacío: se conserva solo {inicio} sin producciones.",
                 "   Los generadores se descartan porque no participan en ninguna derivación desde el inicio."]
    return "\n".join([
        "\n=== Eliminación de símbolos inútiles ===",
        "\n1. No terminales generadores (gramática de entrada):",
        *(razones or ["   Ninguno"]),
        f"   Generadores: {conjunto(generadores)}",
        f"   No generadores: {conjunto(no_generadores)}",
        "   Se eliminan sus producciones y todas las alternativas que los contienen.",
        *aviso,
        "\n2. Alcanzabilidad después de quitar no generadores:",
        f"   Alcanzables: {conjunto(alcanzables)}",
        f"   Generadores descartados: {conjunto(inalcanzables)}",
        f"\n3. Gramática simplificada (inicio: {inicio}):",
        *gramatica,
    ])


def mostrar_pasos_inutiles(inicio, producciones):
    resultado, generadores, alcanzables, pasos = eliminar_inutiles(inicio, producciones)
    print(formatear_pasos_inutiles(inicio, producciones, resultado, generadores, alcanzables, pasos))
    return resultado
