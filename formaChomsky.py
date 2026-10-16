from variables import mostrar_cuerpo


def es_forma_chomsky(inicio, producciones):
    """Comprueba A → a o A → B C, sin excepción para ε.

    El inicio puede aparecer en cuerpos: es la variante sin ε acordada, válida
    para CYK. {inicio: set()} representa el lenguaje vacío y también es válida.
    La clasificación usa las claves de la gramática, no los nombres T/C.
    """
    if inicio not in producciones:
        return False
    no_terminales = set(producciones)
    return all(
        (len(c) == 1 and c[0] not in no_terminales)
        or (len(c) == 2 and all(s in no_terminales for s in c))
        for opciones in producciones.values() for c in opciones
    )


def convertir_chomsky(inicio, producciones):
    """Recibe reglas sin ε ni unitarias y devuelve (reglas, terminales, pasos).

    terminales mapea cada terminal aislado a su auxiliar Tn. pasos contiene
    (lado_izquierdo, cuerpo_normalizado, reglas_binarias) por cuerpo largo.
    Conserva el inicio y no modifica la entrada. No ejecuta fases anteriores.
    """
    if inicio not in producciones:
        raise ValueError("el símbolo inicial debe estar en producciones")
    no_terminales = set(producciones)
    for variable, alternativas in producciones.items():
        for cuerpo in sorted(alternativas):
            if not cuerpo:
                raise ValueError(f"{variable} → ε: elimine todas las producciones ε antes de Chomsky")
            if len(cuerpo) == 1 and cuerpo[0] in no_terminales:
                raise ValueError(f"{variable} → {cuerpo[0]}: elimine las producciones unitarias antes de Chomsky")

    usados = no_terminales | {
        s for alternativas in producciones.values() for c in alternativas for s in c
    }
    indices = {"T": 1, "C": 1}

    def nuevo_simbolo(prefijo):
        while f"{prefijo}{indices[prefijo]}" in usados:
            indices[prefijo] += 1
        nombre = f"{prefijo}{indices[prefijo]}"
        indices[prefijo] += 1
        usados.add(nombre)
        return nombre

    # Solo se aíslan terminales en cuerpos de longitud >= 2.
    # El orden alfabético hace la asignación reproducible.
    a_aislar = sorted({
        s for alternativas in producciones.values() for c in alternativas if len(c) >= 2
        for s in c if s not in no_terminales
    })
    terminales = {terminal: nuevo_simbolo("T") for terminal in a_aislar}
    normalizada = {
        variable: {
            tuple(terminales.get(s, s) for s in c) if len(c) >= 2 else c
            for c in alternativas
        }
        for variable, alternativas in producciones.items()
    }
    normalizada.update({auxiliar: {(terminal,)} for terminal, auxiliar in terminales.items()})

    resultado = {variable: set() for variable in normalizada}
    pasos = []
    for variable in sorted(normalizada):
        for cuerpo in sorted(normalizada[variable]):
            if len(cuerpo) <= 2:
                resultado[variable].add(cuerpo)
                continue
            reglas = []
            actual = variable
            for simbolo in cuerpo[:-2]:
                auxiliar = nuevo_simbolo("C")
                pareja = (simbolo, auxiliar)
                resultado[actual].add(pareja)
                reglas.append((actual, pareja))
                resultado[auxiliar] = set()
                actual = auxiliar
            pareja = cuerpo[-2:]
            resultado[actual].add(pareja)
            reglas.append((actual, pareja))
            pasos.append((variable, cuerpo, reglas))
    return resultado, terminales, pasos


def formatear_pasos_chomsky(inicio, resultado, terminales, pasos):
    terminales_texto = [
        f"   {auxiliar} → {terminal}" for terminal, auxiliar in terminales.items()
    ]
    divisiones = []
    for variable, cuerpo, reglas in pasos:
        divisiones.append(f"   {variable} → {mostrar_cuerpo(cuerpo)}:")
        divisiones.extend(f"      {v} → {mostrar_cuerpo(c)}" for v, c in reglas)
    gramatica = []
    for variable, alternativas in resultado.items():
        texto = " | ".join(mostrar_cuerpo(c) for c in sorted(alternativas))
        gramatica.append(f"   {variable} → {texto or '∅'}")
    estado = "SÍ" if es_forma_chomsky(inicio, resultado) else "NO"
    return "\n".join([
        "\n=== Forma Normal de Chomsky (sin ε) ===",
        "\n1. Terminales aislados en auxiliares Tn:",
        *(terminales_texto or ["   No se requieren"]),
        "\n2. División de cuerpos largos con auxiliares Cn:",
        *(divisiones or ["   No se requiere"]),
        f"\n3. Gramática en Chomsky (inicio: {inicio}):",
        *gramatica,
        f"\n   Cumple A → terminal o A → B C: {estado}",
    ])


def mostrar_pasos_chomsky(inicio, producciones):
    resultado, terminales, pasos = convertir_chomsky(inicio, producciones)
    print(formatear_pasos_chomsky(inicio, resultado, terminales, pasos))
    return resultado
