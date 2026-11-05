<!-- This README is one language at a time. Other versions are linked below. -->

[English](../../README.md) · [中文](README.zh.md) · [Français](README.fr.md) · **Español** · [Русский](README.ru.md) · [العربية](README.ar.md)

<p align="center">
  <img src="../assets/logo_brand.png" width="760" alt="MINEGRID — Power System Made Simple">
</p>

# MINEGRID

### De los modelos eléctricos al razonamiento multimodal

MINEGRID reúne descripciones no lineales detalladas de equipos, imágenes con anotaciones e instrucciones sobre redes. La biblioteca de modelos permite desarrollar un pequeño simulador de investigación; el benchmark multimodal permite estudiar cómo los modelos de visión y lenguaje entienden diagramas de control y redes eléctricas.

## Explorar la colección

- **[Equipos típicos](../../Multimodal/Alpaca%20Data/Apparatus/index.html)** — 14 familias · 46 configuraciones · descripciones HTML
- **[Benchmark multimodal](../../JSON%20Index/README.md)** — 1.429 pares imagen–anotación · 2 tareas · 3 dificultades
- **[Instrucciones complementarias](../../Multimodal/Alpaca%20Data/README.md)** — Instrucciones de redes y un archivo de ejemplo de conocimiento general

## Equipos típicos: contenido de los modelos

Cada página describe estados, parámetros, entradas/salidas, ecuaciones diferenciales y algebraicas, límites no lineales y supuestos. Las configuraciones detalladas y los modos alternativos se presentan por separado. Los HTML son referencias de modelado, no un simulador ejecutable incluido.

| Equipo | Contenido del modelo | Configuraciones |
|---|---|---|
| [Generador síncrono detallado](../../Multimodal/Alpaca%20Data/Apparatus/sg.html) | Dinámica electromagnética de seis devanados, rotor, regulador de velocidad, excitación, PSS y saturación/límites según configuración. | 3 |
| [Convertidor formador de red VSG](../../Multimodal/Alpaca%20Data/Apparatus/gfm_vsg.html) | Inercia virtual, amortiguamiento, potencia/tensión, lazos internos, filtro LCL, enlace CC, límites y anti-windup. | 4 |
| [Control formador de red droop](../../Multimodal/Alpaca%20Data/Apparatus/gfm_droop.html) | Filtrado de potencia, droop P–f, tensión/reactiva, lazos internos, LCL, enlace CC y variantes de secuencia. | 3 |
| [Control formador de red matching](../../Multimodal/Alpaca%20Data/Apparatus/gfm_matching.html) | Sincronización mediante tensión CC, balance energético, regulación tensión/corriente, filtro y actuadores. | 3 |
| [Control formador de red dVOC](../../Multimodal/Alpaca%20Data/Apparatus/gfm_dvoc.html) | Amplitud/fase del oscilador, regulación de potencia, dinámica eléctrica, lazos internos y límites. | 3 |
| [Convertidor seguidor de red PQ](../../Multimodal/Alpaca%20Data/Apparatus/gfl_pq.html) | PLL, potencia activa/reactiva, corriente, LCL/enlace CC, soporte ante fallos y recuperación de potencia. | 4 |
| [Convertidor seguidor de red PU](../../Multimodal/Alpaca%20Data/Apparatus/gfl_pu.html) | PLL, potencia activa y tensión CA, lazos de corriente, dinámica eléctrica y variantes de soporte ante fallos. | 4 |
| [Aerogenerador DFIG formador de red](../../Multimodal/Alpaca%20Data/Apparatus/gfm_dfig.html) | Aerodinámica, transmisión de dos masas, flujos, convertidores, enlace CC, pitch, crowbar/chopper y soporte ante fallos. | 2 |
| [Aerogenerador DFIG seguidor de red](../../Multimodal/Alpaca%20Data/Apparatus/gfl_dfig.html) | Turbina, transmisión y máquina de inducción, PLL y controles de rotor/red, pitch, crowbar y recuperación. | 2 |
| [Aerogenerador PMSG directo formador de red](../../Multimodal/Alpaca%20Data/Apparatus/gfm_pmsg.html) | Máquina de imanes, mecánica, convertidores espalda con espalda y enlace CC; VSG o matching, pitch y soporte ante fallos. | 4 |
| [Aerogenerador PMSG directo seguidor de red](../../Multimodal/Alpaca%20Data/Apparatus/gfl_pmsg.html) | Control de velocidad/corriente de máquina, PLL y tensión CC del lado de red, dinámica electromagnética y pitch. | 2 |
| [Carga de centro de datos](../../Multimodal/Alpaca%20Data/Apparatus/data_center.html) | Cadena AFE–UPS–VSI–PSU, carga computacional equivalente, mediciones/actuadores y energía de batería de respaldo. | 2 |
| [Motor de inducción](../../Multimodal/Alpaca%20Data/Apparatus/induction_motor.html) | Flujos de estator/rotor, velocidad, par de carga, medida de tensión, indicador térmico y protección de subtensión. | 2 |
| [Convertidor de interconexión CA/CC](../../Multimodal/Alpaca%20Data/Apparatus/ic.html) | Intercambio energético CA/CC, PLL, filtro y dinámica CC; modos PQ, EQ, PU y EU con variantes de secuencia. | 8 |

[Directorio de equipos](../../Multimodal/Alpaca%20Data/Apparatus/index.html) · [Convenciones de modelos](../../Multimodal/Alpaca%20Data/Apparatus/model_conventions.html)

## Benchmark multimodal

| Tarea | Fácil | Media | Difícil | Total | Lotes JSONL |
|---|---|---|---|---|---|
| Control de equipos | 76 | 593 | 366 | 1035 | 64 |
| Topología de red | 38 | 222 | 134 | 394 | 25 |
| Total | 114 | 815 | 500 | 1429 | 89 |

Recuento de los archivos actuales: 1.429 muestras, 1.429 imágenes referenciadas y 89 lotes JSONL. Las dificultades no equivalen a particiones de entrenamiento, validación y prueba.

| Colección complementaria | Archivos | Instrucciones |
|---|---|---|
| Network (JSON) | 32000 | 335517 |
| General Knowledge (ejemplo JSON) | 1 | 39 |

Las instrucciones complementarias no forman parte del total multimodal. Apparatus contiene 16 páginas HTML, incluido el índice y las convenciones; General Knowledge conserva un único archivo de ejemplo.

## Vista general de imágenes

Nueve ejemplos representativos por tarea y dificultad, en mosaicos compactos de 3 × 3. El control de equipos ocupa una fila y la topología de redes la siguiente, con los tres niveles de dificultad en paralelo. Haga clic en un mosaico para verlo en resolución completa; los ID permiten rastrear las muestras.

### Control de equipos

| Fácil | Media | Difícil |
|---|---|---|
| [![Control de equipos · Fácil](../assets/apparatus_easy.png)](../assets/apparatus_easy.png) | [![Control de equipos · Media](../assets/apparatus_medium.png)](../assets/apparatus_medium.png) | [![Control de equipos · Difícil](../assets/apparatus_hard.png)](../assets/apparatus_hard.png) |

### Topología de red

| Fácil | Media | Difícil |
|---|---|---|
| [![Topología de red · Fácil](../assets/network_easy.png)](../assets/network_easy.png) | [![Topología de red · Media](../assets/network_medium.png)](../assets/network_medium.png) | [![Topología de red · Difícil](../assets/network_hard.png)](../assets/network_hard.png) |

## Crear un simulador eléctrico de escala inicial

Use los HTML como especificaciones para un primer simulador de escala reducida: interfaz común, unidades y marcos de referencia coherentes, conservación de límites, acoplamiento con las ecuaciones de red, inicialización e integración temporal con eventos. Es una base para prototipos e implementación asistida por LLM, seguida de validación de ingeniería independiente.

### Alineación dinámica con PSCAD y PowerFactory

Cuando se requiera una alineación dinámica de alta fidelidad con modelos de PSCAD, PowerFactory u otros programas similares, las descripciones de TypicalApparatus pueden servir como punto de partida estructural. Los métodos de [Guo y Shi (2024)](https://doi.org/10.1109/CIEEC60922.2024.10583352) y [Shi, Guo et al. (2026)](https://doi.org/10.1109/TSTE.2025.3621702) ofrecen una base para obtener expresiones analíticas explícitas de las ecuaciones del modelo a partir de datos transitorios y restricciones físicas, mediante identificación de modelos y regresión simbólica.

Mantenga las unidades, los sistemas de referencia y las condiciones de contorno coherentes con el modelo de referencia. Valide la generalización en puntos de operación y perturbaciones no utilizados durante la identificación, comparando las respuestas transitorias obtenidas con las del programa de referencia. El código relacionado está disponible en [DSIPS — Dynamic Sparse Identification of Power System](https://github.com/gdg1999/DSIPS).

## Ejemplos de prompts

### 1 · Convertir una descripción en componente

```text
Usa el modelo HTML VSG de MINEGRID adjunto como especificación. Enumera estados, variables algebraicas, entradas, salidas, parámetros, unidades y marcos de referencia. Diseña interfaces para f(x,z,u;p), g(x,z,u;p) y la corriente inyectada. Conserva todos los límites y términos anti-windup. Distingue los valores disponibles de la información ausente; no inventes parámetros. Presenta el plan y la correspondencia ecuación-código antes de programar.
```

### 2 · Construir un primer simulador dinámico

```text
Con las descripciones adjuntas del generador síncrono, GFM, GFL y carga, diseña un simulador de investigación de tres nodos. Define bases comunes, ecuaciones de red, interfaces e inicialización coherente. Añade un pequeño cambio de carga, registro de estados/corrientes/tensiones, comprobaciones de residuos y convergencia del paso. Enumera parámetros y supuestos adicionales no proporcionados. Distingue funciones implementadas de comportamientos no verificados.
```

## Evaluar VLM e investigar sus mecanismos

- Capacidades: reconocimiento de bloques, signos de realimentación, identificación de estados y derivación DAE; extracción de nodos/ramas, conectividad y reconstrucción de tablas.
- Mecanismos: experimentos controlados sobre idioma, resolución, oclusión y posición de símbolos; clasificación de errores perceptivos y de razonamiento físico; análisis de activaciones cuando se dispone del interior del modelo.
- Protocolo: reservar las respuestas de referencia, fijar tareas y dificultades, evaluar estructura y coherencia física y agrupar fuentes compartidas para reducir filtraciones. La coincidencia textual exacta no basta para ecuaciones equivalentes.

## Estructura y formato de anotación

```text
JSON Index/
├── device_control_*/      # JSONL
└── network_topology_*/     # JSONL
Multimodal/
├── Alpaca Data/
│   ├── Apparatus/          # HTML
│   ├── Network/            # JSON
│   └── General Knowledge/  # JSON
├── apparatus_{easy,medium,hard}/
└── network_{easy,medium,hard}/
Scripts/
docs/
├── assets/
└── readme/
```

Cada registro JSONL contiene id, image, conversations y annotations. Las rutas de imagen parten de la raíz. Decodifique de nuevo como JSON el valor de la respuesta del asistente. El prompt original está en chino; annotations ofrece en, es, ar, fr y ru. Los seis idiomas del README no implican seis traducciones independientes de las respuestas. Los JSON complementarios son arreglos de registros instruction/input/output.

[Guía de anotaciones](../../JSON%20Index/README.md) · [Guía de evaluación](../../Scripts/LLM%20Evaluation/README.md)

## Referencia bibliográfica

Si este recurso contribuye a su trabajo, cite el artículo relacionado:

D. Guo, S. Li, X. Shi, S. Jiang, G. Konstantinou and Y. Cao, "A Large Language Model-Based Framework for Automated Dynamic Simulation of Power Systems," in *IEEE Transactions on Smart Grid*, doi: [10.1109/TSG.2026.3731592](https://doi.org/10.1109/TSG.2026.3731592).

```bibtex
@article{guo2026automated,
  author  = {Guo, D. and Li, S. and Shi, X. and Jiang, S. and Konstantinou, G. and Cao, Y.},
  title   = {A Large Language Model-Based Framework for Automated Dynamic Simulation of Power Systems},
  journal = {IEEE Transactions on Smart Grid},
  year    = {2026},
  doi     = {10.1109/TSG.2026.3731592}
}
```

Métodos relacionados de identificación con datos transitorios y agregación con restricciones físicas:

1. D. Guo and X. Shi, "Model Identification of Grid-following System for Stability Evaluation with Transient Data," *2024 IEEE 7th International Electrical and Energy Conference (CIEEC)*, Harbin, China, 2024, pp. 01–06, doi: [10.1109/CIEEC60922.2024.10583352](https://doi.org/10.1109/CIEEC60922.2024.10583352).

2. X. Shi, D. Guo *et al*., "Physical-Informed Detailed Aggregation of Wind Farm Based on Symbolic Regression: Structure, Solution and Generalizability," in *IEEE Transactions on Sustainable Energy*, vol. 17, no. 2, pp. 1511–1524, April 2026, doi: [10.1109/TSTE.2025.3621702](https://doi.org/10.1109/TSTE.2025.3621702).

```bibtex
@inproceedings{guo2024identification,
  author    = {Guo, D. and Shi, X.},
  title     = {Model Identification of Grid-following System for Stability Evaluation with Transient Data},
  booktitle = {2024 IEEE 7th International Electrical and Energy Conference (CIEEC)},
  address   = {Harbin, China},
  year      = {2024},
  pages     = {01--06},
  doi       = {10.1109/CIEEC60922.2024.10583352}
}

@article{shi2026aggregation,
  author  = {Shi, X. and Guo, D. and others},
  title   = {Physical-Informed Detailed Aggregation of Wind Farm Based on Symbolic Regression: Structure, Solution and Generalizability},
  journal = {IEEE Transactions on Sustainable Energy},
  volume  = {17},
  number  = {2},
  pages   = {1511--1524},
  month   = apr,
  year    = {2026},
  doi     = {10.1109/TSTE.2025.3621702}
}
```

## Sitio web de Minegrid

**Sitio web de Minegrid: en pruebas y mantenimiento…**
