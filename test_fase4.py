import io
import unittest
from contextlib import redirect_stdout
from copy import deepcopy
from pathlib import Path

from eliminarEpsilon import eliminar_epsilon
from eliminarUnitarias import eliminar_unitarias
from eliminarInutiles import eliminar_inutiles
from formaChomsky import (
    convertir_chomsky, es_forma_chomsky, formatear_pasos_chomsky,
    mostrar_pasos_chomsky,
)
from gramatica import leer_gramatica
from test_fase1 import lenguaje_acotado


class Fase4Tests(unittest.TestCase):
    def transformar(self, inicio, producciones, limite=4):
        copia = deepcopy(producciones)
        resultado, terminales, pasos = convertir_chomsky(inicio, producciones)
        self.assertEqual(producciones, copia)
        self.assertIn(inicio, resultado)
        self.assertTrue(es_forma_chomsky(inicio, resultado))
        self.assertEqual(lenguaje_acotado(inicio, producciones, limite), lenguaje_acotado(inicio, resultado, limite))
        self.assertEqual(convertir_chomsky(inicio, resultado)[0], resultado)
        self.assertFalse(any(() in opciones for opciones in resultado.values()))
        originales = set(producciones)
        for nuevo in set(resultado) - originales:
            self.assertRegex(nuevo, r"^[TC][1-9][0-9]*$")
        return resultado, terminales, pasos

    def test_terminal_solo_no_se_renombra(self):
        p = {"S": {("eats",)}}
        r, terminales, pasos = self.transformar("S", p)
        self.assertEqual(r, p)
        self.assertEqual(terminales, {})
        self.assertEqual(pasos, [])

    def test_pareja_terminal_no_terminal(self):
        r, terminales, _ = self.transformar("S", {"S": {("a", "B")}, "B": {("b",)}})
        self.assertEqual(terminales, {"a": "T1"})
        self.assertEqual(r["S"], {("T1", "B")})
        self.assertEqual(r["T1"], {("a",)})

    def test_pareja_dos_terminales(self):
        r, terminales, _ = self.transformar("S", {"S": {("she", "eats")}})
        self.assertEqual(terminales, {"eats": "T1", "she": "T2"})
        self.assertEqual(r["S"], {("T2", "T1")})

    def test_reutiliza_terminal_repetido(self):
        r, terminales, _ = self.transformar("S", {"S": {("a", "a"), ("a",)}})
        self.assertEqual(terminales, {"a": "T1"})
        self.assertEqual(r["S"], {("T1", "T1"), ("a",)})

    def test_tres_no_terminales(self):
        p = {"S": {("A", "B", "D")}, "A": {("a",)}, "B": {("b",)}, "D": {("d",)}}
        r, _, pasos = self.transformar("S", p)
        self.assertEqual(r["S"], {("A", "C1")})
        self.assertEqual(r["C1"], {("B", "D")})
        self.assertEqual(len(pasos), 1)

    def test_cuerpo_cuatro_mixto(self):
        p = {"S": {("a", "B", "c", "D")}, "B": {("b",)}, "D": {("d",)}}
        r, terminales, _ = self.transformar("S", p)
        self.assertEqual(terminales, {"a": "T1", "c": "T2"})
        self.assertEqual(r["S"], {("T1", "C1")})
        self.assertEqual(r["C1"], {("B", "C2")})
        self.assertEqual(r["C2"], {("T2", "D")})
        self.assertEqual(lenguaje_acotado("S", r, 4), {("a", "b", "c", "d")})

    def test_cinco_simbolos_conservan_orden(self):
        p = {"S": {("a", "b", "c", "d", "e")}}
        r, _, _ = self.transformar("S", p, limite=5)
        self.assertEqual(lenguaje_acotado("S", r, 5), {tuple("abcde")})
        self.assertEqual({v for v in r if v.startswith("C")}, {"C1", "C2", "C3"})

    def test_colisiones_con_no_terminales(self):
        p = {"S": {("a", "T1", "C1")}, "T1": {("b",)}, "C1": {("c",)}}
        r, terminales, _ = self.transformar("S", p)
        self.assertEqual(terminales, {"a": "T2"})
        self.assertEqual(r["S"], {("T2", "C2")})
        self.assertEqual(r["C1"], p["C1"])
        self.assertEqual(r["T1"], p["T1"])

    def test_colisiones_con_cualquier_simbolo(self):
        # La API también evita símbolos que son terminales internos.
        p = {"S": {("T1", "C1", "a")}}
        r, terminales, _ = self.transformar("S", p)
        self.assertNotIn("T1", terminales.values())
        self.assertNotIn("C1", set(r))
        self.assertIn("C2", r)

    def test_multiples_alternativas_no_mezclan_lenguajes(self):
        p = {"S": {("a", "b", "c"), ("d", "e", "f")}}
        r, _, _ = self.transformar("S", p)
        self.assertEqual(lenguaje_acotado("S", r), {tuple("abc"), tuple("def")})

    def test_inicio_recursivo_sin_epsilon(self):
        p = {"S": {("S", "S"), ("a",)}}
        self.assertTrue(es_forma_chomsky("S", p))
        self.assertEqual(self.transformar("S", p)[0], p)

    def test_gramatica_ya_chomsky_no_cambia(self):
        g = leer_gramatica(Path(__file__).parent / "Ejemplos/1-cnf.txt")
        self.assertEqual(self.transformar(g.inicio, g.producciones)[0], g.producciones)

    def test_lenguaje_vacio(self):
        self.assertEqual(self.transformar("S", {"S": set()})[0], {"S": set()})

    def test_rechaza_epsilon(self):
        with self.assertRaisesRegex(ValueError, "elimine todas las producciones ε"):
            convertir_chomsky("S", {"S": {()}})

    def test_rechaza_unitarias(self):
        with self.assertRaisesRegex(ValueError, "unitarias"):
            convertir_chomsky("S", {"S": {("NP",)}, "NP": {("she",)}})

    def test_inicio_inexistente(self):
        self.assertFalse(es_forma_chomsky("X", {"S": {("a",)}}))
        with self.assertRaisesRegex(ValueError, "inicial"):
            convertir_chomsky("X", {"S": {("a",)}})

    def test_validador_formas_invalidas(self):
        for cuerpo in ((), ("S",), ("a", "S"), ("a", "b"), ("S", "S", "S")):
            with self.subTest(cuerpo=cuerpo):
                self.assertFalse(es_forma_chomsky("S", {"S": {cuerpo}}))

    def test_resultado_no_comparte_conjuntos(self):
        p = {"S": {("a",)}}
        r, _, _ = convertir_chomsky("S", p)
        r["S"].add(("b",))
        self.assertEqual(p, {"S": {("a",)}})

    def test_nombres_reproducibles(self):
        p = {"S": {("a", "B", "c")}, "B": {("b",)}}
        inversa = dict(reversed(list(p.items())))
        self.assertEqual(convertir_chomsky("S", p), convertir_chomsky("S", inversa))

    def test_formatear_sin_imprimir_y_mostrar(self):
        p = {"S": {("a", "b", "c")}}
        datos = convertir_chomsky("S", p)
        salida = io.StringIO()
        with redirect_stdout(salida):
            texto = formatear_pasos_chomsky("S", *datos)
        self.assertEqual(salida.getvalue(), "")
        self.assertIn("T1 → a", texto)
        self.assertIn("C1", texto)
        with redirect_stdout(salida):
            r = mostrar_pasos_chomsky("S", p)
        self.assertEqual(salida.getvalue(), texto + "\n")
        self.assertEqual(r, datos[0])

    def test_pipeline_ejemplos(self):
        base = Path(__file__).parent / "Ejemplos"
        for nombre in ("chomsky.txt", "chomsky_colisiones.txt", "inutiles.txt",
                       "lenguaje_vacio.txt", "ingles.txt", "1-cnf.txt",
                       "Gramatica1.txt", "Gramatica3.txt", "epsilon_inicio.txt"):
            with self.subTest(nombre=nombre):
                g = leer_gramatica(base / nombre)
                sin_epsilon = eliminar_epsilon(g.inicio, g.producciones)[0]
                sin_unitarias = eliminar_unitarias(g.inicio, sin_epsilon)[0]
                simplificada = eliminar_inutiles(g.inicio, sin_unitarias)[0]
                r, _, _ = self.transformar(g.inicio, simplificada)
                self.assertEqual(lenguaje_acotado(g.inicio, r, 4), lenguaje_acotado(g.inicio, g.producciones, 4) - {()})


if __name__ == "__main__":
    unittest.main()
