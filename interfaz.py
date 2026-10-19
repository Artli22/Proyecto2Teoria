"""Interfaz gráfica (Tkinter) para simplificar una gramática, convertirla a
Chomsky y validar cadenas w mediante CYK.

Reutiliza exactamente la misma lógica que main.py (CLI); esta ventana solo
organiza la carga de archivos .txt, aplica un tema visual propio y muestra
los resultados en pestañas con resaltado de texto.
La seguridad de tipo de archivo (gramática vs. cadena) se apoya en los
encabezados %formato/%cadena/%tipo ya validados por archivosEntrada.py y
gramatica.py: cualquier archivo cruzado se rechaza con un mensaje claro.
"""

import re
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, scrolledtext, ttk

from archivosEntrada import leer_cadenas, tokenizar_cadena
from cyk import ejecutar_cyk, formatear_arbol, formatear_proceso_cyk, formatear_tabla, formatear_tabla_piramide
from eliminarEpsilon import formatear_pasos_epsilon
from eliminarInutiles import eliminar_inutiles, formatear_pasos_inutiles
from eliminarUnitarias import eliminar_unitarias, formatear_pasos_unitarias
from formaChomsky import convertir_chomsky, formatear_pasos_chomsky
from gramatica import leer_gramatica
from variables import mostrar_cuerpo

TIPOS_TXT = [("Archivos de texto", "*.txt")]

# ----------------------------------------------------------------- Paleta
BG_APP = "#F4F1FB"
PANEL_BG = "#FFFFFF"
PRIMARY = "#6C4AB6"
PRIMARY_DARK = "#4B3184"
ACCENT = "#17B8A6"
ACCENT_DARK = "#0E8C7D"
TEXT_DARK = "#2E2A4A"
MUTED = "#8B86A8"
SUCCESS = "#1E8E5A"
SUCCESS_LIGHT = "#2ECC71"
DANGER = "#D64550"
WARNING = "#E2A33D"

EDITOR_BG = "#211C3A"
EDITOR_FG = "#E9E6F7"
EDITOR_HEADER = "#6CE3D9"
EDITOR_STEP = "#C9A6FF"
EDITOR_TREE = "#FFD166"
EDITOR_MUTED = "#8E88B0"


def _mezclar_colores(color_a, color_b, proporcion):
    a = tuple(int(color_a[i:i + 2], 16) for i in (1, 3, 5))
    b = tuple(int(color_b[i:i + 2], 16) for i in (1, 3, 5))
    mezcla = tuple(round(x + (y - x) * proporcion) for x, y in zip(a, b))
    return f"#{mezcla[0]:02x}{mezcla[1]:02x}{mezcla[2]:02x}"


class AplicacionCYK(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("🌳 CFG Studio — Simplificación y CYK")
        self.geometry("1040x760")
        self.minsize(820, 560)
        self.configure(bg=BG_APP)

        self.gramatica = None
        self.cadenas = None  # (lineas, formato)
        self.cnf = None
        self.resultados_cyk = []  # [(etiqueta, ResultadoCYK), ...]

        self._configurar_estilo()
        self._construir_widgets()

    # ------------------------------------------------------------ Estilo
    def _configurar_estilo(self):
        estilo = ttk.Style(self)
        try:
            estilo.theme_use("clam")
        except tk.TclError:
            pass

        estilo.configure("TFrame", background=BG_APP)
        estilo.configure("Tarjeta.TFrame", background=PANEL_BG)
        estilo.configure("TLabel", background=BG_APP, foreground=TEXT_DARK, font=("Segoe UI", 10))
        estilo.configure("Panel.TLabel", background=PANEL_BG, foreground=TEXT_DARK, font=("Segoe UI", 10))
        estilo.configure("Muted.TLabel", background=PANEL_BG, foreground=MUTED, font=("Segoe UI", 9, "italic"))
        estilo.configure("Cargado.TLabel", background=PANEL_BG, foreground=SUCCESS, font=("Segoe UI", 9, "bold"))

        estilo.configure("Gramatica.TLabelframe", background=PANEL_BG, borderwidth=2, relief="solid")
        estilo.configure("Gramatica.TLabelframe.Label", background=PANEL_BG, foreground=PRIMARY,
                          font=("Segoe UI", 10, "bold"))
        estilo.configure("Cadenas.TLabelframe", background=PANEL_BG, borderwidth=2, relief="solid")
        estilo.configure("Cadenas.TLabelframe.Label", background=PANEL_BG, foreground=ACCENT_DARK,
                          font=("Segoe UI", 10, "bold"))

        estilo.configure("Gramatica.TButton", background=PRIMARY, foreground="white",
                          font=("Segoe UI", 10, "bold"), padding=(14, 8), borderwidth=0)
        estilo.map("Gramatica.TButton", background=[("active", PRIMARY_DARK)])
        estilo.configure("Cadenas.TButton", background=ACCENT, foreground="white",
                          font=("Segoe UI", 10, "bold"), padding=(14, 8), borderwidth=0)
        estilo.map("Cadenas.TButton", background=[("active", ACCENT_DARK)])
        estilo.configure("Analizar.TButton", background=SUCCESS, foreground="white",
                          font=("Segoe UI", 11, "bold"), padding=(20, 10), borderwidth=0)
        estilo.map("Analizar.TButton", background=[("active", "#166B45")])

        estilo.configure("TCombobox", fieldbackground="white", background=PANEL_BG, padding=4)

        estilo.configure("TNotebook", background=BG_APP, borderwidth=0, tabmargins=(6, 8, 6, 0))
        estilo.configure("TNotebook.Tab", background="#E3DEF7", foreground=PRIMARY_DARK,
                          font=("Segoe UI", 10, "bold"), padding=(16, 10), borderwidth=0)
        estilo.map("TNotebook.Tab", background=[("selected", PRIMARY)], foreground=[("selected", "white")])

        for nombre, color in (("Info", PRIMARY_DARK), ("Ok", ACCENT_DARK), ("Warn", WARNING), ("Error", DANGER)):
            estilo.configure(f"Estado{nombre}.TLabel", background=color, foreground="white",
                              font=("Segoe UI", 9, "bold"), padding=(10, 6))

    # ------------------------------------------------------------------ UI
    def _construir_widgets(self):
        self.banner = tk.Canvas(self, height=74, highlightthickness=0, bg=PRIMARY)
        self.banner.pack(fill="x", side="top")
        self.banner.bind("<Configure>", self._dibujar_banner)

        marco_archivos = ttk.Frame(self, padding=10)
        marco_archivos.pack(fill="x")

        marco_gramatica = ttk.LabelFrame(marco_archivos, text="① Gramática (.txt)", style="Gramatica.TLabelframe",
                                          padding=10)
        marco_gramatica.pack(side="left", fill="both", expand=True, padx=(0, 6))
        ttk.Button(marco_gramatica, text="📂 Cargar gramática...", style="Gramatica.TButton",
                   command=self.cargar_gramatica).pack(anchor="w")
        self.etiqueta_gramatica = ttk.Label(marco_gramatica, text="— Ningún archivo cargado —", style="Muted.TLabel")
        self.etiqueta_gramatica.pack(anchor="w", pady=(6, 0))

        marco_cadena = ttk.LabelFrame(marco_archivos, text="② Cadena(s) w (.txt con %cadena)",
                                       style="Cadenas.TLabelframe", padding=10)
        marco_cadena.pack(side="left", fill="both", expand=True, padx=(6, 0))
        ttk.Button(marco_cadena, text="📝 Cargar cadena(s)...", style="Cadenas.TButton",
                   command=self.cargar_cadenas).pack(anchor="w")
        self.etiqueta_cadena = ttk.Label(marco_cadena, text="— Ningún archivo cargado —", style="Muted.TLabel")
        self.etiqueta_cadena.pack(anchor="w", pady=(6, 0))

        marco_acciones = ttk.Frame(self, padding=(10, 0, 10, 10))
        marco_acciones.pack(fill="x")
        ttk.Button(marco_acciones, text="▶️  Analizar", style="Analizar.TButton", command=self.analizar).pack(
            side="left")
        ttk.Label(marco_acciones, text="   🔎 Cadena a mostrar:").pack(side="left")
        self.combo_cadenas = ttk.Combobox(marco_acciones, state="disabled", width=45)
        self.combo_cadenas.pack(side="left", padx=(4, 0))
        self.combo_cadenas.bind("<<ComboboxSelected>>", lambda _evento: self._mostrar_cadena_seleccionada())

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        self.texto_arbol = self._crear_pestana("🌳  Árbol")
        self.texto_tabla = self._crear_pestana("📊  Tabla CYK")
        self.texto_chomsky = self._crear_pestana("🔗  Forma Chomsky")
        self.texto_simplificacion = self._crear_pestana("✂️  Simplificación")

        self.barra_estado = ttk.Label(self, text="ℹ️  Listo. Carga una gramática para comenzar.", anchor="w",
                                       style="EstadoInfo.TLabel")
        self.barra_estado.pack(fill="x", side="bottom")

    def _dibujar_banner(self, _evento=None):
        self.banner.delete("fondo")
        ancho = self.banner.winfo_width()
        alto = int(self.banner["height"])
        if ancho <= 1:
            return
        for x in range(0, ancho, 3):
            color = _mezclar_colores(PRIMARY, ACCENT, x / max(ancho - 1, 1))
            self.banner.create_line(x, 0, x, alto, fill=color, tags="fondo")
        self.banner.create_text(20, alto / 2 - 11, anchor="w", text="🌳 CFG Studio",
                                 fill="white", font=("Segoe UI", 17, "bold"), tags="fondo")
        self.banner.create_text(22, alto / 2 + 15, anchor="w",
                                 text="Simplificación de gramáticas  •  Forma de Chomsky  •  Análisis CYK",
                                 fill="#EFEBFF", font=("Segoe UI", 9), tags="fondo")
        self.banner.create_text(ancho - 20, alto / 2, anchor="e", text="🧩",
                                 font=("Segoe UI", 26), tags="fondo")

    def _crear_pestana(self, titulo):
        marco = ttk.Frame(self.notebook, style="Tarjeta.TFrame", padding=6)
        self.notebook.add(marco, text=titulo)
        texto = scrolledtext.ScrolledText(marco, wrap="none", font=("Consolas", 10), state="disabled",
                                           bg=EDITOR_BG, fg=EDITOR_FG, insertbackground=EDITOR_FG,
                                           selectbackground=PRIMARY, relief="flat", padx=12, pady=10,
                                           borderwidth=0)
        texto.pack(fill="both", expand=True)
        self._configurar_etiquetas(texto)
        return texto

    def _configurar_etiquetas(self, widget):
        widget.tag_configure("encabezado", foreground=EDITOR_HEADER, font=("Consolas", 10, "bold"))
        widget.tag_configure("paso", foreground=EDITOR_STEP, font=("Consolas", 10, "bold"))
        widget.tag_configure("si", foreground=SUCCESS_LIGHT, font=("Consolas", 10, "bold"))
        widget.tag_configure("no", foreground="#FF6B6B", font=("Consolas", 10, "bold"))
        widget.tag_configure("arbol", foreground=EDITOR_TREE)
        widget.tag_configure("vacio", foreground=EDITOR_MUTED)

    def _escribir(self, widget, contenido):
        widget.configure(state="normal")
        widget.delete("1.0", "end")
        widget.insert("1.0", contenido)
        self._resaltar(widget)
        widget.configure(state="disabled")

    def _resaltar(self, widget):
        total_lineas = int(widget.index("end-1c").split(".")[0])
        for n in range(1, total_lineas + 1):
            inicio, fin = f"{n}.0", f"{n}.end"
            texto_linea = widget.get(inicio, fin)
            despojada = texto_linea.strip()
            if despojada.startswith("===") and despojada.endswith("==="):
                widget.tag_add("encabezado", inicio, fin)
            elif re.match(r"^\d+\.\s", despojada):
                widget.tag_add("paso", inicio, fin)
            elif "Pertenece al lenguaje: SÍ" in texto_linea:
                widget.tag_add("si", inicio, fin)
            elif "Pertenece al lenguaje: NO" in texto_linea:
                widget.tag_add("no", inicio, fin)
            elif any(simbolo in texto_linea for simbolo in ("├──", "└──", "│")):
                widget.tag_add("arbol", inicio, fin)
            elif "∅" in texto_linea or "No hay árbol" in texto_linea:
                widget.tag_add("vacio", inicio, fin)

    def _set_estado(self, mensaje, tipo="info"):
        iconos = {"info": "ℹ️", "ok": "✅", "warn": "⚠️", "error": "❌"}
        estilos = {"info": "EstadoInfo.TLabel", "ok": "EstadoOk.TLabel", "warn": "EstadoWarn.TLabel",
                   "error": "EstadoError.TLabel"}
        self.barra_estado.configure(text=f"{iconos.get(tipo, 'ℹ️')}  {mensaje}", style=estilos.get(tipo, "EstadoInfo.TLabel"))

    # ------------------------------------------------------------- Carga
    def cargar_gramatica(self):
        ruta = filedialog.askopenfilename(title="Seleccionar archivo de gramática", filetypes=TIPOS_TXT)
        if not ruta:
            return
        try:
            gramatica = leer_gramatica(ruta)
        except (ValueError, OSError, UnicodeError) as error:
            messagebox.showerror("Archivo de gramática inválido", str(error))
            self._set_estado("El archivo elegido no es una gramática válida.", "error")
            return
        self.gramatica = gramatica
        self.etiqueta_gramatica.configure(text=f"✅ {Path(ruta).name}", style="Cargado.TLabel")
        self._reiniciar_resultados()
        self._set_estado(f"Gramática cargada: {Path(ruta).name}", "ok")

    def cargar_cadenas(self):
        ruta = filedialog.askopenfilename(title="Seleccionar archivo de cadenas", filetypes=TIPOS_TXT)
        if not ruta:
            return
        try:
            lineas, formato = leer_cadenas(ruta)
        except (ValueError, OSError, UnicodeError) as error:
            messagebox.showerror("Archivo de cadenas inválido", str(error))
            self._set_estado("El archivo elegido no es un archivo de cadenas válido.", "error")
            return
        self.cadenas = (lineas, formato)
        self.etiqueta_cadena.configure(text=f"✅ {Path(ruta).name}", style="Cargado.TLabel")
        self._reiniciar_resultados()
        self._set_estado(f"Cadena(s) cargada(s): {Path(ruta).name}", "ok")

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
            self._set_estado("Cargue una gramática antes de analizar.", "warn")
            return
        try:
            self._procesar_gramatica()
        except ValueError as error:
            messagebox.showerror("Error al procesar la gramática", str(error))
            self._set_estado("Error al procesar la gramática.", "error")
            return
        if self.cadenas is not None:
            if not self._procesar_cadenas():
                return
        else:
            mensaje = "Cargue un archivo de cadenas (.txt con %cadena) y presione Analizar para ejecutar CYK."
            self._escribir(self.texto_tabla, mensaje)
            self._escribir(self.texto_arbol, mensaje)
        self._set_estado("Análisis completado.", "ok")

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
                self._set_estado("Error al ejecutar CYK.", "error")
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
            resumen, formatear_tabla_piramide(resultado), formatear_proceso_cyk(resultado),
        ]))
        self._escribir(self.texto_arbol, "\n\n".join([
            resumen, "Árbol de análisis (gramática en Chomsky):\n" + formatear_arbol(resultado.arbol),
        ]))


def main():
    app = AplicacionCYK()
    app.mainloop()


if __name__ == "__main__":
    main()
