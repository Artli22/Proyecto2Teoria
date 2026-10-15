import argparse
from gramatica import leer_gramatica
from eliminarEpsilon import mostrar_pasos


def main():
    parser = argparse.ArgumentParser(description="Valida una gramática del Laboratorio 7")
    parser.add_argument("archivo", help="archivo de texto con una producción por línea")
    args = parser.parse_args()
    try:
        inicio, producciones = leer_gramatica(args.archivo)
    except (ValueError, OSError) as error:
        parser.exit(1, f"Error: {error}\n")
    print(f"Símbolo inicial: {inicio}")
    for variable, opciones in producciones.items():
        print(f"{variable} → {' | '.join(opciones)}")
    mostrar_pasos(inicio, producciones)


if __name__ == "__main__":
    main()