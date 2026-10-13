# Plan de clase (60 min) — «Memories con LangChain y LlamaIndex»

Sesión breve, con poca carga teórica y una única demo. Materiales: `slides/01_Memories.pdf` (o `.pptx`), `notebooks/02_Demo_Memories_Solucion.ipynb` y `notebooks/03_Reto_Memories_Alumno.ipynb`.

---

## Recorridos de la sesión

| | **Recorrido A** (recomendado para impartir) | **Recorrido B** (opcional) |
|---|---|---|
| Qué | Demo del 02 **sin clave** (modelo determinista claramente identificado) + reto 03/04 | Demo del 02 **con** `GROQ_API_KEY` (LLM real de Groq) |
| Requisitos | Ninguno: sin cuentas, sin claves, sin coste | Cuenta gratuita de Groq y la clave en los Secretos de Colab |
| Qué se ve igual | Guardado, recuperación, aislamiento e inspección del historial: la memoria es la de LangGraph en ambos casos | Lo mismo, con respuestas generadas por el LLM real |

- **Ambos recorridos usan el mismo notebook 02**: si al ejecutarlo detecta clave entra en modo con API; si no, en modo sin API. No hay que preparar nada distinto.
- **Alternativa visual sin Colab:** la app Streamlit (`streamlit run app.py`) reproduce la misma demo en el navegador (chat con memoria, cambio y borrado de sesiones, mapa del almacén). Útil para probar la clase en local o invitar al grupo a tocar la memoria tras la sesión.
- LlamaIndex **no se instala ni se ejecuta**: solo se compara conceptualmente (diapositiva 5 y celda final del 02).

---

## Bloque 0 · Antes de empezar (checklist del formador)

- [ ] Runtime de Colab con `GROQ_API_KEY` en los Secretos (o `OPENAI_API_KEY`). Si no hay clave, la demo corre en **modo sin API** (modelo determinista): se puede impartir igualmente.
- [ ] `slides/01_Memories.pdf` abierto en pantalla completa.
- [ ] Notebook del formador **ejecutado de principio al fin** antes de la sesión (Runtime → Run all).
- [ ] Notebook del reto copiado donde lo tenga el alumnado (enlace de Colab en el README).
- [ ] Reloj visible: los tiempos son orientativos pero la sesión es de 60 min exactos.

---

## 1. 0–5 min · El problema (Diapositiva 1)

**Objetivo:** que el alumnado experimente la falta de contexto antes de ver la teoría.

- **Decir:** «Voy a hacer dos preguntas a un asistente. Fijaos en la segunda.» Mostrar los dos turnos de la diapositiva 1 (o ejecutar en el notebook los turnos 1 y 2 *sin memoria*: se puede hacer con dos invocaciones usando `thread_id` distintos).
- **Preguntar al grupo:** «¿Por qué no se acuerda de quién soy, si yo se lo he dicho?» Dejar 2-3 respuestas.
- **Concluir (1 frase):** «Las llamadas al LLM son stateless: cada llamada empieza de cero. El contexto lo tenemos que guardar y reenviar *nosotros*.»
- **No:** entrar todavía en APIs ni en código.

## 2. 5–15 min · Conceptos fundamentales (Diapositivas 2, 3 y 4)

**Objetivo:** distinguir historial / corto plazo / persistente y ver el flujo.

- **5–10 · Diapositiva 2 — Qué es y qué NO es la memoria conversacional.** Decir: «Es un mecanismo de la aplicación: guardar el historial y reenviarlo en el siguiente prompt.» Recorrer la columna «NO es»: no es que el modelo recuerde, no es RAG, no es una base de conocimiento. *Recordar:* en esta píldora NO tocamos RAG, embeddings ni bases vectoriales (eso ya lo dabais en otras píldoras).
- **10–13 · Diapositiva 3 — Los tres niveles.** Historial (la lista de mensajes de la conversación) · Memoria a corto plazo (sesión/hilo: `checkpointer` + `thread_id`; muere al cerrar) · Memoria persistente (entre sesiones: store/base de datos; requiere diseño y consentimiento). Enfatizar: «Corto plazo = *thread-scoped* en LangChain».
- **13–15 · Diapositiva 4 — Diagrama del flujo.** Seguir la flecha con el dedo: mensaje → historial del hilo → prompt (system + historial + mensaje) → LLM → respuesta → el checkpointer la guarda → siguiente turno. «Sesión nueva = `thread_id` nuevo = historial vacío: así evitamos fugas entre sesiones.»
- **Transición:** «Veámoslo en vivo.»

## 3. 15–30 min · Demo técnica con LangChain (Diapositiva 5)

**Objetivo:** demostrar guardado, recuperación, aislamiento e inspección del historial.

Ejecutar `02_Demo_Memories_Solucion.ipynb` en este orden (todo está en el notebook, no hace falta improvisar):

| Min | Celda | Qué mostrar | Resultado esperado |
|-----|-------|-------------|--------------------|
| 15–17 | Instalación + modo (API / sin API) | Que el entorno está listo y si hay clave | `Modo: CON API` (Groq/OpenAI) o `Modo: SIN API (demo determinista)` |
| 17–19 | `InMemorySaver` + `hilo()` | El diagrama del flujo de la celda markdown | «El checkpointer es el almacén; el `thread_id` es la etiqueta de la sesión» |
| 19–21 | Turno 1 («Me llamo Alex…») | Saludo personalizado | El asistente reconoce a Alex |
| 21–23 | Turno 2 («¿Cómo leo un CSV?») **mismo hilo** | Respuesta coherente: Python + explicación sencilla | «¿Veis? Usa lo que dijo en el turno 1» |
| 23–25 | Turno 3, `thread_id` nuevo | Misma pregunta **sin** contexto | Respuesta genérica, sin Alex |
| 25–27 | `get_state(...)` | El historial impreso, mensaje a mensaje | 6 mensajes en la sesión Alex vs 2 en la nueva |
| 27–28 | `delete_thread(...)` | Borrar el historial de Alex y releer | `[]` mientras la otra sesión sigue intacta |
| 28–30 | Diapositiva 5, parte LlamaIndex | Comparación conceptual, **sin implementar** | `Memory.from_defaults(session_id=...)`: FIFO a corto plazo + *Memory Blocks* a largo plazo |

- **Decir:** «Hemos visto guardado, recuperación, aislamiento y borrado. Es lo que vais a implementar ahora.»
- **Coste:** 4 llamadas cortas; en Groq (nivel gratuito) o con `gpt-4o-mini` el coste es residual, pero siempre revisad la tarifa.

## 4. 30–50 min · Reto práctico (individual o en parejas)

**Objetivo:** implementar la memoria de sesión sin API ni dependencias externas.

- Entregar `notebooks/03_Reto_Memories_Alumno.ipynb` (enlace Colab del README). Enunciado: 3 funciones (`guardar_mensaje`, `obtener_historial`, `borrar_sesion`) + pruebas automáticas.
- **Reglas:** 15–20 min · sin pegar la solución del 04 · las pistas están en desplegables · pueden usar las pruebas del propio notebook para autocomprobarse.
- **Rol del formador:** circular y responder dudas **con preguntas** («¿qué `thread_id` estás usando?», «¿qué te devuelve `get_state`?»), no dando código.
- Si alguien termina antes: que explique a su pareja por qué `session_id` debe entrar en la configuración de cada llamada.

## 5. 50–55 min · Ejecución conjunta de las pruebas

**Objetivo:** corrección automática y objetiva.

- Pedir a todos: **Runtime → Run all** en su notebook del reto.
- Esperado en la celda final: `🎉 ¡TODAS LAS PRUEBAS SUPERADAS! (4/4)`.
- Preguntar: «¿A quién le ha fallado alguna?» — Abrir 1-2 fallos típicos y leer el mensaje del assert (ej.: «A debe ver solo lo suyo» → el `session_id` se estaba ignorando).
- La rúbrica completa está en `docs/rubrica.md`: los 4 tests = los 4 criterios. No se corrige nada más a mano.

## 6. 55–60 min · Conclusión y criterio ético (Diapositiva 6)

- **55–58 · Límites:** el historial crece → ventana de contexto y coste; los datos guardados pueden estar mal o ser sensibles; un `thread_id` compartido = fuga de contexto entre usuarios.
- **58–59 · Criterio ético:** leer o parafrasear el párrafo de `docs/criterio_etico.md`. Frase final: **«Minimiza, aísla, borra: guardar más no es mejor.»**
- **59–60 · Cierre:** tres mensajes clave y preguntas del grupo.
  1. Sin contexto guardado no hay continuidad.
  2. Corto plazo = hilos (`thread_id` + checkpointer); persistente = entre sesiones, con diseño y consentimiento.
  3. Aísla siempre las sesiones y date la posibilidad de borrar.

---

## Respuestas rápidas a preguntas frecuentes del alumnado

- **¿Esto es RAG?** No. RAG usa recuperación sobre documentos; aquí solo gestionamos el historial de la conversación.
- **¿Y si el historial es enorme?** Se poda, se resume o se extraen hechos (LlamaIndex lo hace con *Memory Blocks*). Ejemplo de LangChain: `SummarizationMiddleware`.
- **¿Dónde se guarda en producción?** En el mismo diseño, con un checkpointer persistente (SQLite/Postgres) en lugar de `InMemorySaver`.
- **¿LlamaIndex es muy distinto?** No en la idea: `Memory` con `session_id`, cola FIFO a corto plazo y bloques a largo plazo. Hoy `ChatMemoryBuffer` está obsoleto.
