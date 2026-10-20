# Proyecto no.2: Intérprete de gramáticas mediante CYK
## Teoria de la computacion - seccion 20
#### Integrantes: 
- Arturo Lima-24683
- Saul Castillo-24915
- Esteban Gonzalez-24005

### Introduccion: 
El siguiente proyecto busca representar el proceso completo de simplificacion de gramatica e interpretacion del algoritmo de Coke-Younger-Kasami (CYK) para poder determinar si la cadena w pertenece o no a la gramatica ingresada mediante los archivos .txt

El procedimiento realizado incluye los 4 pasos para simplificar la gramatica del contexto (CFG): eliminacion de epsilon, eliminacion de producciones unarias, eliminacion de inutiles y forma chomsky; aplicar el algoritmo CYK con la gramatica resultante y la cadena w ingresada. Como paso final, se decidio resumir todos los pasos generados en una UI simple para facilitar la interpretacion. 


## 1. Versión y requisitos

| Elemento | Requisito o estado |
| --- | --- |
| Lenguaje | Python 3.10 o posterior. |
| Bibliotecas de terceros | Ninguna. Todas las importaciones externas al proyecto pertenecen a la biblioteca estándar de Python. |
| Archivos de entrada | .txt codificados en UTF-8|

Se utiliza el comando python interfaz.py para poder inciar la UI de la interfaz grafica, tras iniciar se busca en los archivos del computador local para obtener los .txt de gramatica y cadena w. 

## 2. Objetivos y alcance

- Implementar simplificación de gramáticas: ε, unitarias, no generadores e inalcanzables.
- Convertir las reglas simplificadas a Forma Normal de Chomsky.
- Reconocer cadenas mediante programación del algoritmo CYK.
- Explicar el reconocimiento mediante tabla y árbol de derivación.

La aceptación es sintáctica según la gramática elegida; no garantiza que una
frase tenga sentido semántico ni que el vocabulario modele todo el idioma inglés.

## 3. Archivos Python principales.

| Archivo| Responsabilidad | Funciones o estructuras relevantes |
| --- | --- | --- |
| `main.py` | Entrada del programa, argumentos, coordinación de etapas y presentación de cada resultado. | `main()`. |
| `archivosEntrada.py` | Leer archivos .txt y validar encabezados/roles| `leer_documento()`, `leer_cadenas()`, `tokenizar_cadena()`. |
| `variables.py` | Validar una producción textual y convertir sus alternativas a tuplas de símbolos. | `analizar_linea()`, `mostrar_cuerpo()`, `EPSILON`. |
| `gramatica.py` | Reunir todas las producciones, seleccionar el formato y validar referencias a no terminales. | `Gramatica`, `leer_gramatica()`, `_interpretar()`. |
| `eliminarEpsilon.py` | Calcular anulables y generar combinaciones de omisión sin conservar ε. | `encontrar_anulables()`, `eliminar_epsilon()`, `mostrar_pasos()`. |
| `eliminarUnitarias.py` | Calcular cierres de reglas A → B y copiar sus alternativas no unitarias. | `es_unitaria()`, `encontrar_cierres_unitarios()`, `eliminar_unitarias()`. |
| `eliminarInutiles.py` | Eliminar primero no generadores y después inalcanzables. | `encontrar_generadores()`, `eliminar_no_generadores()`, `encontrar_alcanzables()`, `eliminar_inutiles()`. |
| `formaChomsky.py` | Aislar terminales compuestos con Tn, dividir cuerpos largos con Cn y validar la forma final. | `convertir_chomsky()`, `es_forma_chomsky()`. |
| `cyk.py` | Reconocer tokens, guardar referencias, construir un árbol y formatear tabla/proceso/resultados. | `ejecutar_cyk()`, `ResultadoCYK`, `NodoArbol`, `formatear_tabla()`, `formatear_proceso_cyk()`, `formatear_arbol()`. |

## 4. Importaciones de la biblioteca estándar

| Importación | Archivo donde se utiliza | Finalidad |
| --- | --- | --- |
| `import argparse` | `main.py` | Interpretar rutas, opciones y combinaciones válidas de argumentos de consola. |
| `from pathlib import Path` | `archivosEntrada.py`, `gramatica.py` | Manejar rutas, comprobar extensión y abrir archivos. |
| `import re` | `variables.py` | Validar la estructura de producciones y símbolos mediante expresiones regulares. |
| `from itertools import product` | `eliminarEpsilon.py` | Generar todas las decisiones de conservar/omitir posiciones anulables. |
| `from dataclasses import dataclass` | `gramatica.py`, `cyk.py` | Definir contenedores de datos para la gramática, resultados, referencias y nodos. |
| `from time import perf_counter` | `cyk.py` | Medir el tiempo transcurrido de construcción/llenado de tabla y decisión CYK. |

## 5. Archivos y encabezados de entrada

| Encabezado | Uso |
| --- | --- |
| `%formato libre` | Gramática con símbolos completos separados por espacios. |
| `%formato compacto` | Gramática con un símbolo por carácter. |
| `%cadena libre` | Archivo de w: una palabra por token. |
| `%cadena compacto` | Archivo de w: un carácter por token. |

Cada línea no vacía del archivo de cadenas representa una w. Un archivo que
solo contiene su encabezado representa una w vacía y produce "no pertenece" como respuesta. Las líneas vacías entre cadenas se ignoran.

Los no terminales se escriben con inicial mayúscula y deben estar declarados.
Se aceptan las flechas ->, → y ::=; la primera producción establece el inicio
Las alternativas vacías se rechazan; ε debe escribirse explícitamente. 


## 6. Ejemplo  en inglés: visitas y observación
Archivo `Lab7Teoria/Ejemplos/gramatica_visitas.txt`:

```text
%formato libre
S -> Sentence
Sentence -> NP VP
NP -> Det N | she | he
VP -> V NP | V NP PP
PP -> P NP
V -> visits | sees
N -> student | teacher | museum | garden
Det -> the | a
P -> near | with
```

La regla S → Sentence permite comprobar eliminación de unitarias. El cuerpo
V NP PP permite comprobar binarización. No hay producciones ε ni terminales
mezclados en cuerpos compuestos, por lo que en este caso no hacen falta Tn.

Después de simplificar, Sentence desaparece por inalcanzable y Chomsky incluye:

```text
S -> NP VP
VP -> V NP | V C1
C1 -> NP PP
```

Las restantes reglas léxicas y binarias válidas se conservan.

Archivo `Lab7Teoria/Ejemplos/cadenas_visitas.txt`:

```text
%cadena libre
She visits the museum
The student sees a teacher near the garden
she sees near the museum
the student visits
she visits the library
```

### Resultados verificados

| Cadena w | Resultado CYK | Explicación |
| --- | --- | --- |
| She visits the museum | SÍ | Sujeto she, verbo visits y objeto the museum. |
| The student sees a teacher near the garden | SÍ | Sujeto y objeto con determinante; complemento preposicional permitido. |
| she sees near the museum | NO | Todo el vocabulario existe, pero falta el objeto NP antes del complemento. |
| the student visits | NO | El verbo necesita un objeto según las reglas de VP. |
| she visits the library | NO | library no pertenece al vocabulario de esta gramática. |

Los cinco casos se ejecutaron mediante main.py y el flujo completo. Todos
mostraron tabla y proceso CYK; las cadenas rechazadas no se filtraron antes.

## 7. Interpretación de la salida

Por cada w se muestra:

1. Frase normalizada, peretenece al lenguaje: SÍ/NO.
2. Tabla triangular: fila = longitud, columna = posición inicial desde 1.
3. Llenado por longitudes con fragmentos, reglas y cortes.
4. Comprobación final de pertenencia del inicio a X[1,n].
5. Árbol con ramas si existe derivación; explicación de ausencia si fue NO.

## 8. Discusión y decisiones de diseño

### Símbolos frente a caracteres

El modelo inicial por caracteres no distingue una palabra de varias letras.
Se utilizan tuplas de símbolos completos para admitir NP, Det y palabras como
museum. Compacto se conserva para ejemplos heredados; libre permite palabras.

### Eliminación total de ε

La decisión explícita de excluir ε mantiene todas las fases posteriores sin
producciones vacías. Un conjunto vacío de alternativas es distinto de una
alternativa (). 

### Ciclos y orden de limpieza

Los cierres unitarios y el alcance usan visitados para evitar recorridos
infinitos. Se eliminan no generadores antes de inalcanzables.

## 9. Detalles importantes

- Se utiliza el comando `python interfaz.py` para iniciar el programa con la interfaz gráfica.
- Se necesita que los archivos de Gramática y Cadena tengan sus respectivos encabezados `%formato espacios`, `%formato compacto`, `%cadena compacta` y `%cadena libre` para ser detectados correctamente por las medidas de seguridad de la interfaz.
- Las medidas de seguridad prohiben que se suba una gramática en el segmento de cadenas y una cadena en el segmento de gramática; salta un aviso si no se cumplen estas características.
- Se recomienda utilizar el archivo `prueba1.txt` para la gramática y el archivo `cadena.txt` para verificar casos donde w sí pertenece a la gramática; estos archivos están dentro de la carpeta `Ejemplos/` del proyecto.
- Se recomienda utilizar el archivo `prueba1.txt` para la gramática y el archivo `cadenas_mixtas.txt` para observar casos donde w no pertenece a la gramática; también están incluidos en la carpeta `Ejemplos/`.

## 10. Investigación y toma de decisiones detalladas

El siguiente documento de Word amplía la información presentada en este README sobre la investigación y la toma de decisiones del proyecto. Además, incluye las secciones adicionales requeridas en el documento de instrucciones.

[Consultar el documento de investigación y documentación del proyecto CYK](https://uvggt-my.sharepoint.com/:w:/r/personal/lim24683_uvg_edu_gt/Documents/Investigacion%20y%20documentacion%20proyecto%202%20CYK.docx?d=w178977a787274a0e9b7a2d6d13364d09&csf=1&web=1&e=sylSzX)
