import argparse

from eliminarEpsilon import mostrar_pasos
from eliminarUnitarias import mostrar_pasos_unitarias
from eliminarInutiles import mostrar_pasos_inutiles
from formaChomsky import mostrar_pasos_chomsky
from cyk import ejecutar_cyk, tokenizar_frase, formatear_resultado_cyk
from archivosEntrada import leer_cadenas, tokenizar_cadena
from gramatica import leer_gramatica
from variables import mostrar_cuerpo


def main():
    parser = argparse.ArgumentParser(description="Simplifica una CFG y valida frases mediante CYK con árbol y tiempo")
    parser.add_argument("archivo", help="archivo de producciones")
    parser.add_argument("cadenas", nargs="?", help="archivo .txt con %%cadena libre/compacto y una w por línea")
    parser.add_argument("--formato", choices=("auto", "libre", "espacios", "compacto"), default="auto",
                        help="auto detecta el formato; una opción explícita prevalece sobre el encabezado")
    entrada = parser.add_mutually_exclusive_group()
    entrada.add_argument("--frase", help="frase entre comillas; si falta, se solicita por consola")
    entrada.add_argument("--solo-gramatica", action="store_true", help="mostrar fases 0 a 4 sin solicitar una frase")
    parser.add_argument("--tabla", action="store_true", default=True,
                        help="compatibilidad: la tabla y su llenado ya se muestran por defecto")
    parser.add_argument("--respetar-mayusculas", action="store_true", help="no convertir la frase a minúsculas")
    args = parser.parse_args()
    if args.cadenas is not None and (args.frase is not None or args.solo_gramatica):
        parser.error("el archivo de cadenas no se combina con --frase ni --solo-gramatica")
    entradas_archivo = None
    try:
        gramatica = leer_gramatica(args.archivo, args.formato)
        if args.cadenas is not None:
            entradas_archivo = leer_cadenas(args.cadenas)
    except (ValueError, OSError, UnicodeError) as error:
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
    if entradas_archivo is not None:
        lineas, formato_cadena = entradas_archivo
        for numero, texto in lineas:
            etiqueta = f"línea {numero}" if numero is not None else "cadena vacía"
            print(f"\nArchivo de cadenas: {args.cadenas} ({etiqueta})")
            tokens = tokenizar_cadena(texto, formato_cadena, minusculas=not args.respetar_mayusculas)
            # No hay filtro de pertenencia ni de vocabulario antes de CYK.
            resultado = ejecutar_cyk(gramatica.inicio, cnf, tokens)
            print(formatear_resultado_cyk(resultado, mostrar_tabla=args.tabla))
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