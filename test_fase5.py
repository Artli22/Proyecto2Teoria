import io
import itertools
import subprocess
import sys
import unittest
from contextlib import redirect_stdout
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch

from cyk import (
    ejecutar_cyk, tokenizar_frase, formatear_arbol, formatear_tabla,
    formatear_resultado_cyk,
)
from eliminarEpsilon import eliminar_epsilon
from eliminarUnitarias import eliminar_unitarias
from eliminarInutiles import eliminar_inutiles
from formaChomsky import convertir_chomsky
from gramatica import leer_gramatica
from test_fase1 import lenguaje_acotado


BASE = Path(__file__).parent


def preparar_archivo(nombre):
    g = leer_gramatica(BASE / "Ejemplos" / nombre)
    p = eliminar_epsilon(g.inicio, g.producciones)[0]
    p = eliminar_unitarias(g.inicio, p)[0]
    p = eliminar_inutiles(g.inicio, p)[0]
    return g.inicio, convertir_chomsky(g.inicio, p)[0]


class Fase5Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.inicio_ingles, cls.ingles = preparar_archivo("ingles.txt")

    def verificar_arbol(self, resultado, producciones):
        self.assertEqual(resultado.arbol.simbolo, resultado.inicio)
        hojas = []
        pendientes = [resultado.arbol]
        while pendientes:
            nodo = pendientes.pop()
            if nodo.hijos:
                cuerpo = tuple(h.simbolo for h in nodo.hijos)
                self.assertIn(cuerpo, producciones[nodo.simbolo])
                pendientes.extend(reversed(nodo.hijos))
            else:
                hojas.append(nodo.simbolo)
        self.assertEqual(tuple(hojas), resultado.tokens)

    def ejecutar(self, inicio, producciones, tokens):
        copia = deepcopy(producciones)
        tokens = tuple(tokens)
        r = ejecutar_cyk(inicio, producciones, tokens)
        self.assertEqual(producciones, copia)
        self.assertEqual(r.tokens, tokens)
        self.assertGreaterEqual(r.tiempo_segundos, 0)
        self.assertEqual(len(r.tabla), len(tokens) * (len(tokens) + 1) // 2)
        if r.aceptada:
            self.verificar_arbol(r, producciones)
        else:
            self.assertIsNone(r.arbol)
        return r

    def test_terminal_unico(self):
        r = self.ejecutar("S", {"S": {("she",)}}, ("she",))
        self.assertTrue(r.aceptada)
        self.assertEqual(set(r.tabla[0, 1]), {"S"})

    def test_aceptadas_enunciado(self):
        for frase in ("She eats a cake with a fork", "The cat drinks the beer"):
            with self.subTest(frase=frase):
                r = self.ejecutar(self.inicio_ingles, self.ingles, tokenizar_frase(frase))
                self.assertTrue(r.aceptada)

    def test_otras_aceptadas(self):
        for frase in ("he cooks", "she cuts the meat with a knife", "the dog eats the soup in the oven"):
            with self.subTest(frase=frase):
                self.assertTrue(self.ejecutar("S", self.ingles, tokenizar_frase(frase)).aceptada)

    def test_rechazadas(self):
        for frase in ("she eats a", "the cat the beer", "she eats pizza", "eats she"):
            with self.subTest(frase=frase):
                self.assertFalse(self.ejecutar("S", self.ingles, tokenizar_frase(frase)).aceptada)

    def test_entrada_vacia(self):
        r = self.ejecutar("S", self.ingles, ())
        self.assertFalse(r.aceptada)
        self.assertEqual(r.tabla, {})

    def test_lenguaje_vacio(self):
        self.assertFalse(self.ejecutar("S", {"S": set()}, ("she",)).aceptada)

    def test_vocabulario_desconocido(self):
        r = self.ejecutar("S", self.ingles, ("pizza",))
        self.assertFalse(r.aceptada)
        self.assertEqual(r.tabla[0, 1], {})

    def test_palabra_completa_no_caracteres(self):
        p = {"S": {("eats",)}}
        self.assertTrue(self.ejecutar("S", p, ("eats",)).aceptada)
        self.assertFalse(self.ejecutar("S", p, tuple("eats")).aceptada)

    def test_orden_importa(self):
        p = {"S": {("A", "B")}, "A": {("a",)}, "B": {("b",)}}
        self.assertTrue(self.ejecutar("S", p, ("a", "b")).aceptada)
        self.assertFalse(self.ejecutar("S", p, ("b", "a")).aceptada)

    def test_corte_distinto_del_centro(self):
        p = {"S": {("A", "X")}, "X": {("B", "C")}, "A": {("a",)}, "B": {("b",)}, "C": {("c",)}}
        r = self.ejecutar("S", p, tuple("abc"))
        self.assertTrue(r.aceptada)
        self.assertEqual(r.tabla[0, 3]["S"].corte, 1)

    def test_ambiguedad_conserva_un_arbol(self):
        p = {"S": {("S", "S"), ("a",)}}
        r = self.ejecutar("S", p, ("a",) * 4)
        self.assertTrue(r.aceptada)
        self.assertEqual(r.tabla[0, 4]["S"].corte, 1)
        self.assertEqual(r.arbol, ejecutar_cyk("S", p, ("a",) * 4).arbol)

    def test_multiples_padres_lexicales_y_binarios(self):
        p = {"S": {("A", "B")}, "X": {("A", "B")}, "A": {("a",)}, "B": {("b",)}, "C": {("a",)}}
        r = self.ejecutar("S", p, ("a", "b"))
        self.assertEqual(set(r.tabla[0, 1]), {"A", "C"})
        self.assertEqual(set(r.tabla[0, 2]), {"S", "X"})

    def test_referencias_de_cada_celda(self):
        r = self.ejecutar("S", self.ingles, tokenizar_frase("she eats a cake"))
        for (i, j), celda in r.tabla.items():
            for variable, ref in celda.items():
                if ref.terminal is not None:
                    self.assertEqual(j, i + 1)
                    self.assertEqual(ref.terminal, r.tokens[i])
                    self.assertIn((ref.terminal,), self.ingles[variable])
                else:
                    self.assertLess(i, ref.corte)
                    self.assertLess(ref.corte, j)
                    self.assertIn(ref.izquierda, r.tabla[i, ref.corte])
                    self.assertIn(ref.derecha, r.tabla[ref.corte, j])
                    self.assertIn((ref.izquierda, ref.derecha), self.ingles[variable])

    def test_arbol_con_auxiliares_T_C(self):
        inicio, p = preparar_archivo("chomsky.txt")
        r = self.ejecutar(inicio, p, tuple("abcd"))
        self.assertTrue(r.aceptada)
        texto = formatear_arbol(r.arbol)
        self.assertIn("T1", texto)
        self.assertIn("C1", texto)

    def test_cnf_expresiones_con_id(self):
        inicio, p = preparar_archivo("1-cnf.txt")
        self.assertTrue(self.ejecutar(inicio, p, ("id", "+", "id", "*", "id")).aceptada)
        self.assertTrue(self.ejecutar(inicio, p, ("(", "id", ")")).aceptada)
        self.assertFalse(self.ejecutar(inicio, p, ("id", "+")).aceptada)

    def test_tokenizacion_mayusculas_y_blancos(self):
        self.assertEqual(tokenizar_frase("  She\tEATS  a cake\n"), ("she", "eats", "a", "cake"))
        self.assertEqual(tokenizar_frase("She", minusculas=False), ("She",))
        self.assertEqual(tokenizar_frase(" \t"), ())

    def test_puntuacion_no_se_elimina(self):
        tokens = tokenizar_frase("she eats a cake.")
        self.assertEqual(tokens[-1], "cake.")
        self.assertFalse(self.ejecutar("S", self.ingles, tokens).aceptada)

    def test_api_cyk_no_normaliza(self):
        self.assertFalse(self.ejecutar("S", self.ingles, ("She", "eats")).aceptada)

    def test_rechaza_gramaticas_no_cnf(self):
        gramaticas = ({"S": {()}}, {"S": {("S",)}}, {"S": {("a", "b")}}, {"S": {("S", "S", "S")}})
        for p in gramaticas:
            with self.subTest(p=p), self.assertRaisesRegex(ValueError, "CYK requiere"):
                ejecutar_cyk("S", p, ("a",))

    def test_inicio_no_declarado(self):
        with self.assertRaises(ValueError):
            ejecutar_cyk("X", {"S": {("a",)}}, ("a",))

    def test_tokens_invalidos(self):
        with self.assertRaises(TypeError):
            ejecutar_cyk("S", self.ingles, "she eats")
        for tokens in (("",), (1,), (None,)):
            with self.assertRaises(ValueError):
                ejecutar_cyk("S", self.ingles, tokens)

    def test_tiempo_en_segundos(self):
        with patch("cyk.perf_counter", side_effect=[10.0, 10.125]):
            r = ejecutar_cyk("S", {"S": {("a",)}}, ("a",))
        self.assertEqual(r.tiempo_segundos, 0.125)
        self.assertIn("125.000000 ms", formatear_resultado_cyk(r))

    def test_formatos_no_imprimen(self):
        r = self.ejecutar("S", {"S": {("a",)}}, ("a",))
        salida = io.StringIO()
        with redirect_stdout(salida):
            arbol = formatear_arbol(r.arbol)
            tabla = formatear_tabla(r)
            texto = formatear_resultado_cyk(r, mostrar_tabla=True)
        self.assertEqual(salida.getvalue(), "")
        self.assertIn("S", arbol)
        self.assertIn("[0, 1)", tabla)
        self.assertIn("Pertenece al lenguaje: SÍ", texto)
        self.assertIn("Tabla CYK", texto)

    def test_formato_rechazo_y_vacia(self):
        r = self.ejecutar("S", {"S": set()}, ())
        texto = formatear_resultado_cyk(r, mostrar_tabla=True)
        self.assertIn("Pertenece al lenguaje: NO", texto)
        self.assertIn("No hay árbol", texto)
        self.assertIn("Vacía: no hay tokens", texto)

    def test_contra_oraculo_independiente(self):
        gramaticas = [
            {"S": {("a",)}},
            {"S": {("S", "S"), ("a",), ("b",)}},
            {"S": {("A", "B")}, "A": {("a",)}, "B": {("b",)}},
            {"S": {("A", "S"), ("b",)}, "A": {("a",)}},
            {"S": set()},
        ]
        entradas = [t for n in range(5) for t in itertools.product(("a", "b"), repeat=n)]
        for p in gramaticas:
            esperado = lenguaje_acotado("S", p, 4)
            for tokens in entradas:
                with self.subTest(p=p, tokens=tokens):
                    r = self.ejecutar("S", p, tokens)
                    self.assertEqual(r.aceptada, tokens in esperado)


class Fase5CLITests(unittest.TestCase):
    def comando(self, *argumentos, entrada=None):
        # Ejecuta el CLI real; no usa shell ni depende de su directorio actual.
        return subprocess.run(
            [sys.executable, "-B", "-X", "utf8", str(BASE / "main.py"), *argumentos],
            cwd=BASE, input=entrada, capture_output=True, text=True,
            encoding="utf-8", timeout=20,
        )

    def test_frase_en_argumento(self):
        r = self.comando("Ejemplos/ingles.txt", "--frase", "She eats a cake", "--tabla")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("Pertenece al lenguaje: SÍ", r.stdout)
        self.assertIn("Tabla CYK", r.stdout)
        self.assertIn("Árbol de análisis", r.stdout)

    def test_frase_interactiva(self):
        r = self.comando("Ejemplos/ingles.txt", entrada="The cat drinks the beer\n")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("Pertenece al lenguaje: SÍ", r.stdout)

    def test_rechazo_es_resultado_no_error(self):
        r = self.comando("Ejemplos/ingles.txt", "--frase", "she eats pizza")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("Pertenece al lenguaje: NO", r.stdout)

    def test_entrada_vacia_interactiva(self):
        r = self.comando("Ejemplos/ingles.txt", entrada="\n")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("Pertenece al lenguaje: NO", r.stdout)

    def test_solo_gramatica_no_solicita_entrada(self):
        r = self.comando("Ejemplos/chomsky.txt", "--solo-gramatica", entrada="")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertNotIn("Ingrese una frase", r.stdout)
        self.assertNotIn("Resultado CYK", r.stdout)

    def test_eof_explicativo(self):
        r = self.comando("Ejemplos/ingles.txt", entrada="")
        self.assertEqual(r.returncode, 1)
        self.assertIn("--frase o --solo-gramatica", r.stderr)
        self.assertNotIn("Traceback", r.stderr)

    def test_opciones_incompatibles(self):
        r = self.comando("Ejemplos/ingles.txt", "--solo-gramatica", "--frase", "she eats")
        self.assertEqual(r.returncode, 2)

    def test_respetar_mayusculas(self):
        r = self.comando("Ejemplos/ingles.txt", "--frase", "She eats", "--respetar-mayusculas")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("Pertenece al lenguaje: NO", r.stdout)


if __name__ == "__main__":
    unittest.main()
