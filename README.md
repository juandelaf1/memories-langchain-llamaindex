# Memories con LangChain y LlamaIndex

Repositorio de la píldora **«Orquestación de flujos con LangChain/LlamaIndex: Memories»** (60 minutos).

## Objetivo

Al terminar la sesión, el alumnado sabe explicar y demostrar:

1. Por qué una aplicación necesita gestionar el contexto para mantener la continuidad entre llamadas a un LLM (las llamadas son *stateless*).
2. La diferencia entre **historial conversacional**, **memoria a corto plazo** (sesión/*thread*) y **memoria persistente** (entre sesiones).
3. Cómo se guarda, recupera e inspecciona el historial de una conversación con LangChain (`create_agent` + `checkpointer=InMemorySaver()` + `thread_id`).
4. Cómo evitar que dos sesiones compartan accidentalmente su contexto (un `thread_id` por conversación).
5. Límites, costes y riesgos de esa memoria (ventana de contexto, coste por token, datos sensibles, borrado).

Comparación **conceptual** con LlamaIndex (`Memory`, memoria a corto y largo plazo). No se tocan RAG, embeddings, chunking ni bases vectoriales: esos temas pertenecen a otras píldoras del itinerario.

## Prerrequisitos

- **Nivel:** saber Python básico y haber usado un chatbot con LLM.
- **Cuenta:** Google Colab (gratuito) y, opcionalmente, una API key de **Groq** (nivel gratuito) o **OpenAI** (de pago). *Sin clave, todo funciona en modo demo determinista.*
- **Instalación:** los notebooks instalan ellos mismos las dependencias fijadas (ver `requirements.txt`). No hace falta instalar nada previamente.
- **Tiempo de la actividad:** el reto dura 10-20 minutos.

## Estructura del repositorio

```
memories-langchain-llamaindex/
├── README.md                                  ← este archivo
├── requirements.txt                           ← versiones probadas
├── slides/
│   ├── 01_Memories.pptx                       ← presentación (editable, con notas del ponente)
│   └── 01_Memories.pdf                        ← presentación (versión de reparto)
├── notebooks/
│   ├── 02_Demo_Memories_Solucion.ipynb        ← demo del formador (LangChain real, con o sin API)
│   ├── 03_Reto_Memories_Alumno.ipynb          ← reto del alumnado (sin API, con tests)
│   └── 04_Reto_Memories_Solucion.ipynb        ← solucionario (mismos tests)
└── docs/
    ├── plan_de_clase.md                       ← guion minutado de los 60 minutos
    ├── rubrica.md                             ← 4 criterios = 4 tests
    ├── criterio_etico.md                      ← ficha de criterio ético
    └── troubleshooting.md                     ← errores frecuentes y soluciones
```

## Entregables

| Entregable | Archivo |
|------------|---------|
| Presentación (reparto) | [`slides/01_Memories.pdf`](slides/01_Memories.pdf) |
| Presentación (editable) | [`slides/01_Memories.pptx`](slides/01_Memories.pptx) |
| Notebook del formador | [`notebooks/02_Demo_Memories_Solucion.ipynb`](notebooks/02_Demo_Memories_Solucion.ipynb) |
| Notebook del alumnado | [`notebooks/03_Reto_Memories_Alumno.ipynb`](notebooks/03_Reto_Memories_Alumno.ipynb) |
| Solucionario del reto | [`notebooks/04_Reto_Memories_Solucion.ipynb`](notebooks/04_Reto_Memories_Solucion.ipynb) |
| Plan de clase y guion | [`docs/plan_de_clase.md`](docs/plan_de_clase.md) |
| Rúbrica (corrección automática) | [`docs/rubrica.md`](docs/rubrica.md) |
| Criterio ético | [`docs/criterio_etico.md`](docs/criterio_etico.md) |
| Troubleshooting | [`docs/troubleshooting.md`](docs/troubleshooting.md) |

## Abrir los notebooks en Google Colab

Colab no puede ejecutar notebooks que solo están en tu disco: súbelos al repositorio en GitHub o arrástralos a [colab.research.google.com](https://colab.research.google.com).

Si el repositorio está publicado en GitHub, los botones abren directamente cada notebook:

| Notebook | Abrir en Colab |
|----------|----------------|
| Demo del formador | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/juandelaf1/memories-langchain-llamaindex/blob/main/notebooks/02_Demo_Memories_Solucion.ipynb) |
| Reto del alumnado | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/juandelaf1/memories-langchain-llamaindex/blob/main/notebooks/03_Reto_Memories_Alumno.ipynb) |
| Solucionario | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/juandelaf1/memories-langchain-llamaindex/blob/main/notebooks/04_Reto_Memories_Solucion.ipynb) |

> Si el repositorio vive en otra cuenta o tiene otro nombre, cambia `juandelaf1/memories-langchain-llamaindex` en los enlaces anteriores.
> Alternativa sin GitHub: en Colab, *Archivo → Subir notebook* y elige el archivo `.ipynb`.

## Ejecutar la demo

### A) Con API (LLM real)

1. Consigue una clave: [console.groq.com/keys](https://console.groq.com/keys) (nivel gratuito) o [platform.openai.com/api-keys](https://platform.openai.com/api-keys).
2. En Colab: icono de candado en la barra lateral izquierda → **Secrets** → *Add secret* → nombre `GROQ_API_KEY` (o `OPENAI_API_KEY`) → pega el valor. **Nunca** pegues la clave en una celda ni la subas al repositorio.
3. Abre `02_Demo_Memories_Solucion.ipynb` y haz **Runtime → Run all**.
4. La primera celda instala las versiones fijadas; la celda de entorno imprime `Modo: CON API` y el proveedor detectado.

La demo realiza **4 llamadas cortas** al modelo con un prompt de sistema que limita la respuesta a ~60 palabras: coste residual (en Groq, nivel gratuito). Revisa siempre la tarifa de tu proveedor; el historial completo se reenvía en cada turno, así que en conversaciones largas el coste crece.

### B) Sin API (alternativa determinista, siempre disponible)

- Si **no** detecta ninguna clave, el notebook entra solo en **modo sin API**: usa un modelo simulado (una clase propia de LangChain `BaseChatModel`) que responde en función del historial que recibe.
- Lo que se demuestra es idéntico: **el guardado, la recuperación, el aislamiento y el borrado los hace LangChain/LangGraph** (`InMemorySaver` + `thread_id`); solo está simulada la generación del texto del LLM.
- Sirve para preparar la sesión, para quien no tenga clave y para ejecutar el notebook de principio al fin sin coste.

```bash
# Ejecución local equivalente (sin pasar por Colab)
pip install -r requirements.txt
jupyter nbconvert --to notebook --execute notebooks/02_Demo_Memories_Solucion.ipynb
```

## Completar y corregir la actividad (reto)

1. El alumnado abre `03_Reto_Memories_Alumno.ipynb` en Colab.
2. Implementa **3 funciones** con `TODO` (pistas progresivas en desplegables): `guardar_mensaje`, `obtener_historial`, `borrar_sesion`.
3. **Runtime → Run all**. La última celda imprime el resultado:
   - `🎉 ¡TODAS LAS PRUEBAS SUPERADAS! (4/4)` → superado.
   - `❌ n/4 pruebas fallidas` → cada línea indica el test y el motivo del `assert`.
4. La rúbrica es literalmente esa salida: 4 tests = 4 criterios (`docs/rubrica.md`). No se corrige nada más a mano.
5. El formador tiene `04_Reto_Memories_Solucion.ipynb` con los **mismos tests** resueltos y comentados.

El reto **no necesita API keys, cuentas ni conexión a ningún servicio de IA**: usa la misma maquinaria de memoria (checkpointer + `thread_id`) sin modelo.

## Documentación oficial consultada

- LangChain — visión general de memoria: <https://docs.langchain.com/oss/python/concepts/memory>
- LangChain — memoria a corto plazo (`create_agent` + checkpointer): <https://docs.langchain.com/oss/python/langchain/short-term-memory>
- Referencia — `RunnableWithMessageHistory`: <https://reference.langchain.com/python/langchain-core/runnables/history/RunnableWithMessageHistory>
- LangChain — memoria a largo plazo (stores): <https://docs.langchain.com/oss/python/langchain/long-term-memory>
- LlamaIndex — ejemplo de `Memory`: <https://developers.llamaindex.ai/python/examples/memory/memory/>
- LlamaIndex — memoria de agentes: <https://developers.llamaindex.ai/python/framework/module_guides/deploying/agents/memory/>

## Enlaces internos rápidos

- ¿Algo falla? → [`docs/troubleshooting.md`](docs/troubleshooting.md)
- ¿Cómo impartirla? → [`docs/plan_de_clase.md`](docs/plan_de_clase.md)
- ¿Qué datos podemos guardar? → [`docs/criterio_etico.md`](docs/criterio_etico.md)
