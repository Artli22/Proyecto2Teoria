import argparse

from eliminarEpsilon import mostrar_pasos
from eliminarUnitarias import mostrar_pasos_unitarias
from eliminarInutiles import mostrar_pasos_inutiles
from formaChomsky import mostrar_pasos_chomsky
from cyk import ejecutar_cyk, tokenizar_frase, formatear_resultado_cyk
from gramatica import leer_gramatica
from variables import mostrar_cuerpo


def main():
    parser = argparse.ArgumentParser(description="Simplifica una CFG y valida frases mediante CYK con árbol y tiempo")
    parser.add_argument("archivo", help="archivo de producciones")
    parser.add_argument("--formato", choices=("auto", "espacios", "compacto"), default="auto",
                        help="auto detecta el formato; una opción explícita prevalece sobre el encabezado")
    entrada = parser.add_mutually_exclusive_group()
    entrada.add_argument("--frase", help="frase entre comillas; si falta, se solicita por consola")
    entrada.add_argument("--solo-gramatica", action="store_true", help="mostrar fases 0 a 4 sin solicitar una frase")
    parser.add_argument("--tabla", action="store_true", help="mostrar también la tabla CYK")
    parser.add_argument("--respetar-mayusculas", action="store_true", help="no convertir la frase a minúsculas")
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
    cnf = mostrar_pasos_chomsky(gramatica.inicio, simplificada)
    if args.solo_gramatica:
        return
    frase = args.frase
    if frase is None:
        try:
            frase = input("\nIngrese una frase (palabras separadas por espacios): ")
        except EOFError:
            parser.exit(1, "\nNo se recibió una frase. Use --frase o --solo-gramatica.\n")
        except KeyboardInterrupt:
            parser.exit(130, "\nEntrada cancelada.\n")
    tokens = tokenizar_frase(frase, minusculas=not args.respetar_mayusculas)
    try:
        resultado = ejecutar_cyk(gramatica.inicio, cnf, tokens)
    except (ValueError, TypeError) as error:
        parser.exit(1, f"Error: {error}\n")
    print(formatear_resultado_cyk(resultado, mostrar_tabla=args.tabla))


if __name__ == "__main__":
    main()
