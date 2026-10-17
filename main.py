import argparse
from pathlib import Path

from cadena import leer_cadena, validar_cadena
from eliminarEpsilon import mostrar_pasos
from eliminarUnitarias import mostrar_pasos_unitarias
from eliminarInutiles import mostrar_pasos_inutiles
from formaChomsky import mostrar_pasos_chomsky
from gramatica import leer_gramatica
from variables import mostrar_cuerpo


# Pide la ruta de un archivo si no se pasó como argumento
def solicitar_ruta(valor, mensaje):
    if valor:
        return valor
    try:
        return input(mensaje).strip().strip('"')
    except EOFError:
        return ""


def main():
    parser = argparse.ArgumentParser(description="Simplifica una CFG y la convierte a Forma Normal de Chomsky sin ε")
    parser.add_argument("archivo", nargs="?", help="archivo de producciones (se pide si se omite)")
    parser.add_argument("cadena", nargs="?", help="archivo con la cadena w (se pide si se omite)")
    parser.add_argument("--formato", choices=("auto", "espacios", "compacto"), default="auto",
                        help="auto detecta el formato; una opción explícita prevalece sobre el encabezado")
    args = parser.parse_args()
    ruta_gramatica = solicitar_ruta(args.archivo, "Archivo de la gramática (.txt): ")
    ruta_cadena = solicitar_ruta(args.cadena, "Archivo de la cadena w (.txt): ")
    if not ruta_gramatica or not ruta_cadena:
        parser.exit(1, "Error: se requieren el archivo de la gramática y el de la cadena w\n")
    if Path(ruta_gramatica).resolve() == Path(ruta_cadena).resolve():
        parser.exit(1, "Error: se indicó el mismo archivo para la gramática y la cadena w\n")
    try:
        gramatica = leer_gramatica(ruta_gramatica, args.formato)
        w = leer_cadena(ruta_cadena, gramatica.terminales)
        desconocidos = validar_cadena(w, gramatica)
    except (ValueError, OSError) as error:
        parser.exit(1, f"Error: {error}\n")
    print(f"Cadena w: {mostrar_cuerpo(w)} ({len(w)} símbolos)")
    if desconocidos:
        print(f"Aviso: símbolos que no son terminales de la gramática: {', '.join(desconocidos)}")
    print(f"\nSímbolo inicial: {gramatica.inicio}")
    for variable, opciones in gramatica.producciones.items():
        print(f"{variable} → {' | '.join(mostrar_cuerpo(c) for c in sorted(opciones))}")
    print("\n=== Eliminación de ε (se excluye la cadena vacía) ===")
    sin_epsilon = mostrar_pasos(gramatica.inicio, gramatica.producciones)
    sin_unitarias = mostrar_pasos_unitarias(gramatica.inicio, sin_epsilon)
    simplificada = mostrar_pasos_inutiles(gramatica.inicio, sin_unitarias)
    mostrar_pasos_chomsky(gramatica.inicio, simplificada)


if __name__ == "__main__":
    main()