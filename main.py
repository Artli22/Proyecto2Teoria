import argparse

from eliminarEpsilon import mostrar_pasos
from eliminarUnitarias import mostrar_pasos_unitarias
from eliminarInutiles import mostrar_pasos_inutiles
from formaChomsky import mostrar_pasos_chomsky
from gramatica import leer_gramatica
from variables import mostrar_cuerpo


def main():
    parser = argparse.ArgumentParser(description="Simplifica una CFG y la convierte a Forma Normal de Chomsky sin ε")
    parser.add_argument("archivo", help="archivo de producciones")
    parser.add_argument("--formato", choices=("auto", "espacios", "compacto"), default="auto",
                        help="auto detecta el formato; una opción explícita prevalece sobre el encabezado")
    args = parser.parse_args()
    try:
        gramatica = leer_gramatica(args.archivo, args.formato)
    except (ValueError, OSError) as error:
        parser.exit(1, f"Error: {error}\n")
    print(f"Símbolo inicial: {gramatica.inicio}")
    for variable, opciones in gramatica.producciones.items():
        print(f"{variable} → {' | '.join(mostrar_cuerpo(c) for c in sorted(opciones))}")
    print("\n=== Eliminación de ε (se excluye la cadena vacía) ===")
    sin_epsilon = mostrar_pasos(gramatica.inicio, gramatica.producciones)
    sin_unitarias = mostrar_pasos_unitarias(gramatica.inicio, sin_epsilon)
    simplificada = mostrar_pasos_inutiles(gramatica.inicio, sin_unitarias)
    mostrar_pasos_chomsky(gramatica.inicio, simplificada)


if __name__ == "__main__":
    main()