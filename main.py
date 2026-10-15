import argparse

from eliminarEpsilon import mostrar_pasos
from gramatica import leer_gramatica
from variables import mostrar_cuerpo


def main():
    parser = argparse.ArgumentParser(description="Lee una CFG y muestra la eliminación de ε")
    parser.add_argument("archivo", help="archivo de producciones")
    parser.add_argument("--formato", choices=("auto", "espacios", "compacto"), default="auto")
    args = parser.parse_args()
    try:
        gramatica = leer_gramatica(args.archivo, args.formato)
    except (ValueError, OSError) as error:
        parser.exit(1, f"Error: {error}\n")
    print(f"Símbolo inicial: {gramatica.inicio}")
    for variable, opciones in gramatica.producciones.items():
        print(f"{variable} → {' | '.join(mostrar_cuerpo(c) for c in sorted(opciones))}")
    mostrar_pasos(gramatica.inicio, gramatica.producciones)


if __name__ == "__main__":
    main()
