"""Interfaz gráfica (Tkinter) para simplificar una gramática, convertirla a
Chomsky y validar cadenas w mediante CYK.

Reutiliza exactamente la misma lógica que main.py (CLI); esta ventana solo
organiza la carga de archivos .txt y muestra los resultados en pestañas.
La seguridad de tipo de archivo (gramática vs. cadena) se apoya en los
encabezados %formato/%cadena/%tipo ya validados por archivosEntrada.py y
gramatica.py: cualquier archivo cruzado se rechaza con un mensaje claro.
"""

import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, scrolledtext, ttk

from archivosEntrada import leer_cadenas, tokenizar_cadena
from cyk import ejecutar_cyk, formatear_arbol, formatear_proceso_cyk, formatear_tabla
from eliminarEpsilon import formatear_pasos_epsilon
from eliminarInutiles import eliminar_inutiles, formatear_pasos_inutiles
from eliminarUnitarias import eliminar_unitarias, formatear_pasos_unitarias
from formaChomsky import convertir_chomsky, formatear_pasos_chomsky
from gramatica import leer_gramatica
from variables import mostrar_cuerpo

TIPOS_TXT = [("Archivos de texto", "*.txt")]


class AplicacionCYK(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Simplificación de gramáticas y análisis CYK")
        self.geometry("1000x700")
        self.minsize(760, 520)

        self.gramatica = None
        self.cadenas = None  # (lineas, formato)
        self.cnf = None
        self.resultados_cyk = []  # [(etiqueta, ResultadoCYK), ...]

        self._construir_widgets()

    # ------------------------------------------------------------------ UI
    def _construir_widgets(self):
        marco_archivos = ttk.Frame(self, padding=10)
        marco_archivos.pack(fill="x")

        marco_gramatica = ttk.LabelFrame(marco_archivos, text="1. Gramática (.txt)", padding=8)
        marco_gramatica.pack(side="left", fill="both", expand=True, padx=(0, 5))
        ttk.Button(marco_gramatica, text="Cargar gramática...", command=self.cargar_gramatica).pack(anchor="w")
        self.etiqueta_gramatica = ttk.Label(marco_gramatica, text="Ningún archivo cargado", foreground="#555")
        self.etiqueta_gramatica.pack(anchor="w", pady=(4, 0))

        marco_cadena = ttk.LabelFrame(marco_archivos, text="2. Cadena(s) w (.txt con %cadena)", padding=8)
        marco_cadena.pack(side="left", fill="both", expand=True, padx=(5, 0))
        ttk.Button(marco_cadena, text="Cargar cadena(s)...", command=self.cargar_cadenas).pack(anchor="w")
        self.etiqueta_cadena = ttk.Label(marco_cadena, text="Ningún archivo cargado", foreground="#555")
        self.etiqueta_cadena.pack(anchor="w", pady=(4, 0))

        marco_acciones = ttk.Frame(self, padding=(10, 0, 10, 10))
        marco_acciones.pack(fill="x")
        ttk.Button(marco_acciones, text="Analizar", command=self.analizar).pack(side="left")
        ttk.Label(marco_acciones, text="   Cadena a mostrar:").pack(side="left")
        self.combo_cadenas = ttk.Combobox(marco_acciones, state="disabled", width=45)
        self.combo_cadenas.pack(side="left", padx=(2, 0))
        self.combo_cadenas.bind("<<ComboboxSelected>>", lambda _evento: self._mostrar_cadena_seleccionada())

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        self.texto_arbol = self._crear_pestana("Árbol")
        self.texto_tabla = self._crear_pestana("Tabla CYK")
        self.texto_chomsky = self._crear_pestana("Forma Chomsky")
        self.texto_simplificacion = self._crear_pestana("Simplificación")

        self.barra_estado = ttk.Label(self, text="Listo.", anchor="w", relief="sunken", padding=(6, 2))
        self.barra_estado.pack(fill="x", side="bottom")

    def _crear_pestana(self, titulo):
        marco = ttk.Frame(self.notebook)
        self.notebook.add(marco, text=titulo)
        texto = scrolledtext.ScrolledText(marco, wrap="none", font=("Consolas", 10), state="disabled")
        texto.pack(fill="both", expand=True)
        return texto

    def _escribir(self, widget, contenido):
        widget.configure(state="normal")
        widget.delete("1.0", "end")
        widget.insert("1.0", contenido)
        widget.configure(state="disabled")

    # ------------------------------------------------------------- Carga
    def cargar_gramatica(self):
        ruta = filedialog.askopenfilename(title="Seleccionar archivo de gramática", filetypes=TIPOS_TXT)
        if not ruta:
            return
        try:
            gramatica = leer_gramatica(ruta)
        except (ValueError, OSError, UnicodeError) as error:
            messagebox.showerror("Archivo de gramática inválido", str(error))
            return
        self.gramatica = gramatica
        self.etiqueta_gramatica.configure(text=Path(ruta).name, foreground="#000")
        self._reiniciar_resultados()
        self.barra_estado.configure(text=f"Gramática cargada: {ruta}")

    def cargar_cadenas(self):
        ruta = filedialog.askopenfilename(title="Seleccionar archivo de cadenas", filetypes=TIPOS_TXT)
        if not ruta:
            return
        try:
            lineas, formato = leer_cadenas(ruta)
        except (ValueError, OSError, UnicodeError) as error:
            messagebox.showerror("Archivo de cadenas inválido", str(error))
            return
        self.cadenas = (lineas, formato)
        self.etiqueta_cadena.configure(text=Path(ruta).name, foreground="#000")
        self._reiniciar_resultados()
        self.barra_estado.configure(text=f"Cadena(s) cargada(s): {ruta}")

    def _reiniciar_resultados(self):
        self.cnf = None
        self.resultados_cyk = []
        self.combo_cadenas.configure(state="disabled", values=())
        self.combo_cadenas.set("")
        for widget in (self.texto_arbol, self.texto_tabla, self.texto_chomsky, self.texto_simplificacion):
            self._escribir(widget, "")

    # --------------------------------------------------------- Análisis
    def analizar(self):
        if self.gramatica is None:
            messagebox.showwarning("Falta la gramática", "Cargue primero un archivo de gramática (.txt).")
            return
        try:
            self._procesar_gramatica()
        except ValueError as error:
            messagebox.showerror("Error al procesar la gramática", str(error))
            return
        if self.cadenas is not None:
            if not self._procesar_cadenas():
                return
        else:
            mensaje = "Cargue un archivo de cadenas (.txt con %cadena) y presione Analizar para ejecutar CYK."
            self._escribir(self.texto_tabla, mensaje)
            self._escribir(self.texto_arbol, mensaje)
        self.barra_estado.configure(text="Análisis completado.")

    def _procesar_gramatica(self):
        inicio = self.gramatica.inicio
        sin_epsilon, texto_epsilon = formatear_pasos_epsilon(inicio, self.gramatica.producciones)
        sin_unitarias, cierres, incorporaciones = eliminar_unitarias(inicio, sin_epsilon)
        texto_unitarias = formatear_pasos_unitarias(inicio, sin_unitarias, cierres, incorporaciones)
        simplificada, generadores, alcanzables, pasos_inutiles = eliminar_inutiles(inicio, sin_unitarias)
        texto_inutiles = formatear_pasos_inutiles(
            inicio, sin_unitarias, simplificada, generadores, alcanzables, pasos_inutiles
        )
        cnf, terminales, pasos_chomsky = convertir_chomsky(inicio, simplificada)
        texto_chomsky = formatear_pasos_chomsky(inicio, cnf, terminales, pasos_chomsky)

        encabezado = "\n".join([
            f"Símbolo inicial: {inicio}",
            *(
                f"{variable} → {' | '.join(mostrar_cuerpo(c) for c in sorted(opciones))}"
                for variable, opciones in self.gramatica.producciones.items()
            ),
        ])
        texto_simplificacion = "\n".join([
            encabezado,
            "\n=== Eliminación de ε (se excluye la cadena vacía) ===",
            texto_epsilon,
            texto_unitarias,
            texto_inutiles,
        ])
        self._escribir(self.texto_simplificacion, texto_simplificacion)
        self._escribir(self.texto_chomsky, texto_chomsky)
        self.cnf = cnf

    def _procesar_cadenas(self):
        lineas, formato = self.cadenas
        resultados = []
        opciones = []
        for numero, texto in lineas:
            etiqueta = f"Línea {numero}: {texto}" if numero is not None else "(cadena vacía)"
            tokens = tokenizar_cadena(texto, formato, minusculas=True)
            try:
                resultado = ejecutar_cyk(self.gramatica.inicio, self.cnf, tokens)
            except (ValueError, TypeError) as error:
                messagebox.showerror("Error al ejecutar CYK", f"{etiqueta}: {error}")
                return False
            resultados.append((etiqueta, resultado))
            opciones.append(etiqueta)
        self.resultados_cyk = resultados
        self.combo_cadenas.configure(state="readonly", values=opciones)
        self.combo_cadenas.current(0)
        self._mostrar_cadena_seleccionada()
        return True

    def _mostrar_cadena_seleccionada(self):
        if not self.resultados_cyk:
            return
        indice = self.combo_cadenas.current()
        if indice < 0:
            indice = 0
        _etiqueta, resultado = self.resultados_cyk[indice]
        frase = " ".join(resultado.tokens) or "(vacía)"
        resumen = "\n".join([
            f"Frase analizada: {frase}",
            f"Pertenece al lenguaje: {'SÍ' if resultado.aceptada else 'NO'}",
            f"Tiempo CYK: {resultado.tiempo_segundos * 1000:.6f} ms",
        ])
        self._escribir(self.texto_tabla, "\n\n".join([
            resumen, formatear_tabla(resultado), formatear_proceso_cyk(resultado),
        ]))
        self._escribir(self.texto_arbol, "\n\n".join([
            resumen, "Árbol de análisis (gramática en Chomsky):\n" + formatear_arbol(resultado.arbol),
        ]))


def main():
    app = AplicacionCYK()
    app.mainloop()


if __name__ == "__main__":
    main()
