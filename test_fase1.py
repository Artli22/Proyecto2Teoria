import io
import unittest
from contextlib import redirect_stdout
from copy import deepcopy
from pathlib import Path

from eliminarEpsilon import eliminar_epsilon, encontrar_anulables, mostrar_pasos
from gramatica import leer_gramatica


def lenguaje_acotado(inicio, producciones, limite=3):
    """Oráculo de pruebas: punto fijo de palabras, independiente del algoritmo ε.

    No limita pasos de derivación: resuelve también ciclos y reglas unitarias.
    Solo limita la longitud en terminales, por lo que no prueba equivalencia
    para longitudes mayores al límite.
    """
    lenguajes = {v: set() for v in producciones}
    while True:
        cambio = False
        for variable, alternativas in producciones.items():
            for cuerpo in alternativas:
                palabras = {()}
                for simbolo in cuerpo:
                    opciones = lenguajes[simbolo] if simbolo in lenguajes else {(simbolo,)}
                    palabras = {a + b for a in palabras for b in opciones if len(a + b) <= limite}
                nuevos = palabras - lenguajes[variable]
                if nuevos:
                    lenguajes[variable].update(nuevos)
                    cambio = True
        if not cambio:
            return lenguajes[inicio]


class Fase1Tests(unittest.TestCase):
    def transformar(self, inicio, producciones):
        original = deepcopy(producciones)
        resultado, anulables, pasos, combinaciones = eliminar_epsilon(inicio, producciones)
        self.assertEqual(producciones, original)
        self.assertEqual(set(resultado), set(producciones))
        self.assertFalse(any(() in opciones for opciones in resultado.values()))
        self.assertEqual(
            lenguaje_acotado(inicio, producciones) - {()},
            lenguaje_acotado(inicio, resultado),
        )
        return resultado, anulables

    def test_epsilon_directo(self):
        r, _ = self.transformar("S", {"S": {(), ("a",)}})
        self.assertEqual(r, {"S": {("a",)}})

    def test_solo_epsilon(self):
        r, _ = self.transformar("S", {"S": {()}})
        self.assertEqual(r, {"S": set()})

    def test_indirectos_y_ciclos(self):
        _, anulables = self.transformar("S", {"S": {("NP",)}, "NP": {("Det",)}, "Det": {("NP",), ()}})
        self.assertEqual(anulables, {"S", "NP", "Det"})

    def test_repetidos(self):
        r, _ = self.transformar("S", {"S": {("NP", "NP")}, "NP": {(), ("she",)}})
        self.assertEqual(r["S"], {("NP", "NP"), ("NP",)})

    def test_recursion(self):
        self.transformar("S", {"S": {("S", "S"), ("a",), ()}})

    def test_lenguaje_vacio(self):
        self.transformar("S", {"S": {("A",)}, "A": {("S",)}})

    def test_sin_epsilon_y_terminal_e(self):
        r, anulables = self.transformar("S", {"S": {("e",)}})
        self.assertEqual(anulables, set())
        self.assertEqual(r, {"S": {("e",)}})

    def test_idempotencia(self):
        r, _ = self.transformar("S", {"S": {(), ("a",)}})
        self.assertEqual(eliminar_epsilon("S", r)[0], r)

    def test_presentacion(self):
        salida = io.StringIO()
        with redirect_stdout(salida):
            resultado = mostrar_pasos("S", {"S": {()}})
        self.assertEqual(resultado, {"S": set()})
        self.assertIn("∅", salida.getvalue())

    def test_ejemplos(self):
        base = Path(__file__).parent / "Ejemplos"
        for nombre in ("Gramatica1.txt", "Gramatica3.txt", "ingles.txt", "epsilon_inicio.txt"):
            with self.subTest(nombre=nombre):
                g = leer_gramatica(base / nombre)
                self.transformar(g.inicio, g.producciones)


if __name__ == "__main__":
    unittest.main()
