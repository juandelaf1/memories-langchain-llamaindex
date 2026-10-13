# Troubleshooting — píldora «Memories con LangChain y LlamaIndex»

Errores más probables al ejecutar `02_Demo_Memories_Solucion.ipynb` (formador) o los notebooks del reto (`03` alumno / `04` solución).
Cada caso indica **síntoma → causa probable → solución concreta**.

---

## 1. Instalaciones e incompatibilidades de versiones

| # | Síntoma | Causa probable | Solución |
|---|---------|----------------|----------|
| 1.1 | `ModuleNotFoundError: No module named 'langchain'` o `'langgraph'` | No se ejecutó la celda de instalación o el kernel no es el que tiene los paquetes | Ejecuta la primera celda (`%pip install -q "langchain==1.4.3" "langchain-core==1.6.6" "langgraph==1.2.12" ...`), comprueba con `import langchain, langgraph; print(langchain.__version__)` y, en Colab, **Runtime → Restart session** si Colab lo pide, y vuelve a *Run all*. |
| 1.2 | `pip` tarda mucho, cambia otros paquetes o el entorno deja de funcionar | Instalación sin fijar versiones en un entorno que ya tenía LangChain | Usa siempre las versiones fijadas (celda del notebook o `requirements.txt`). Para limpiar: `%pip uninstall -y langchain langchain-core langgraph langchain-openai langchain-groq` y reinstala con las versiones fijadas. |
| 1.3 | Aviso `A newer version of ... is available` | Solo es un aviso, no un error | No hace falta actualizar. Las versiones del notebook están probadas juntas. |
| 1.4 | `ERROR: Could not find a version that satisfies the requirement langchain==1.4.3` | Python demasiado antiguo o réplica de pip caída | Usa un runtime de Colab estándar (Python ≥ 3.10) o repite la instalación; no fuerces versiones más viejas sin probarlas. |
| 1.5 | Local: instalaste en un Python y ejecutas en otro | Distintos intérpretes (conda vs sistema) | Ejecuta `import sys; print(sys.executable)` en el notebook y compáralo con el `python` donde instalaste. En Jupyter, reinstala el kernel: `python -m ipykernel install --user`. |

## 2. Imports que cambian entre versiones

| # | Síntoma | Causa probable | Solución |
|---|---------|----------------|----------|
| 2.1 | `ImportError: cannot import name 'ConversationChain' / 'ConversationBufferMemory'` | Sigues un tutorial antiguo de LangChain 0.1/0.2 | En LangChain 1.x la memoria a corto plazo se hace con `create_agent(..., checkpointer=InMemorySaver())` + `thread_id`. Ese es el enfoque de esta píldora. |
| 2.2 | `ModuleNotFoundError: No module named 'langgraph.checkpoint.memory'` | `langgraph` ausente o versión incompatible | `%pip install -q langgraph==1.2.12` y reinicia el kernel. |
| 2.3 | `cannot import name 'InMemorySaver' from 'langgraph.checkpoint.memory'` | Mezcla de paquetes de versiones distintas | Reinstala con los pins del punto 1.2; comprueba con `pip show langgraph langchain langchain-core`. |
| 2.4 | Dudas sobre `RunnableWithMessageHistory` | API válida para **cadenas** (`Runnable`), no para agentes | Sigue existiendo en `langchain_core.runnables.history`, pero en esta píldora el historial lo gestiona el agente: `agent.get_state(config).values["messages"]`. Documentación: <https://reference.langchain.com/python/langchain-core/runnables/history/RunnableWithMessageHistory> |

## 3. API key ausente o inválida

| # | Síntoma | Causa probable | Solución |
|---|---------|----------------|----------|
| 3.1 | El notebook imprime **«Modo sin API»** cuando esperabas el LLM real | No hay `GROQ_API_KEY` ni `OPENAI_API_KEY` ni en el entorno ni en los Secretos de Colab | En Colab: icono de candado (*Secrets*) → *Add secret* → nombre `GROQ_API_KEY` (o `OPENAI_API_KEY`) → pega el valor → reinicia el runtime y *Run all*. En local: exporta la variable **en la terminal antes de arrancar Jupyter**, nunca dentro del notebook. |
| 3.2 | `AuthenticationError` / `401` / `Error code: 401 - invalid_api_key` | Clave copiada incompleta, con espacios o revocada | Vuelve a crear la clave en la consola del proveedor y rehaz el secreto. No la pegues nunca en una celda del notebook ni en el repositorio. |
| 3.3 | El notebook se queda esperando `Introduce GROQ_API_KEY:` en una ejecución automática | `getpass` no tiene terminal cuando ejecutas con `nbclient`/`papermill` | Define la variable de entorno antes de ejecutar, o pulsa **Enter** para continuar en modo sin API (la demo determinista funciona igual). |
| 3.4 | `ModuleNotFoundError: No module named 'langchain_groq'` / `'langchain_openai'` | Falta el paquete del proveedor elegido | Instala los pins completos del notebook (`langchain-groq==1.1.3`, `langchain-openai==1.6.7`). |
| 3.5 | `NotFoundError: The model ... does not exist` | El identificador del modelo ya no existe en el proveedor | Cambia la variable del modelo en la celda del agente: en Groq lista los disponibles con `python -c "from groq import Groq; print([m.id for m in Groq().models.list().data])"`; en OpenAI usa un modelo de tu cuenta (p. ej. `gpt-4o-mini`). |

## 4. Cuotas y límites del proveedor

| # | Síntoma | Causa probable | Solución |
|---|---------|----------------|----------|
| 4.1 | `429`, `rate_limit_exceeded`, `quota exceeded` | Límite de peticiones por minuto o saldo agotado | Espera unos segundos y reejecuta solo las celdas de la demo (4 llamadas). Groq tiene nivel gratuito con límites; OpenAI requiere saldo. |
| 4.2 | La demo va muy lenta o falla a mitad | Pico de carga del proveedor | Reejecuta desde la celda del agente; el `InMemorySaver` sigue en memoria, pero si reiniciaste el kernel vuelve a ejecutar *Run all*. |
| 4.3 | Preocupación por el coste | El historial crece y cada turno reenvía todos los mensajes | La demo son 4 turnos cortos: coste mínimo. En producción, aplica poda/resumen (ver `SummarizationMiddleware` en la doc de LangChain) y revisa la tarifa de tu proveedor. |

## 5. Identificadores de hilo (`thread_id`) incorrectos

| # | Síntoma | Causa probable | Solución |
|---|---------|----------------|----------|
| 5.1 | El segundo turno no recuerda nada pese a ser «la misma conversación» | Se invocó con otro `thread_id` o **sin la configuración** (`invoke(...)` sin el segundo argumento) | Reutiliza exactamente `cfg = {"configurable": {"thread_id": "sesion-alex"}}` y pásalo como segundo argumento. Verifica: `agente.get_state(cfg).values`. |
| 5.2 | Dos sesiones comparten historial / falla el test de aislamiento | Todas las conversaciones usan el mismo `thread_id` (o el valor se ignora) | Un id único por sesión. En el reto, `session_id` debe entrar en la config de **cada** llamada. |
| 5.3 | Typo: `thread_id` vs `threadid`, o `config` en vez de `configurable` | Claves del diccionario de configuración mal escritas | Copia literalmente `{"configurable": {"thread_id": ...}}`. LangGraph ignora claves desconocidas y crea un hilo «fantasma» sin datos. |
| 5.4 | En el reto: `AttributeError: ... checkpointer` o `delete_thread` | Grafo compilado sin checkpointer, o `almacen` recreado dentro de la función | Usa `crear_almacen()` del notebook tal cual está definido y no crees almacenes nuevos dentro de las funciones a implementar. |

## 6. Confusión entre historial, estado y respuesta

| # | Síntoma | Causa probable | Solución |
|---|---------|----------------|----------|
| 6.1 | `KeyError: 'messages'` o ves solo el último texto | Se confunde la **respuesta** con el **historial** | `r = agent.invoke(...)` devuelve el estado completo: `r["messages"][-1].content` es solo la última respuesta; el historial es `r["messages"]` (o `agent.get_state(cfg).values["messages"]`). |
| 6.2 | «Hice 2 preguntas y hay 4 mensajes» | Cada turno añade 2 mensajes (usuario + asistente) | Es correcto. En el reto, cada `guardar_mensaje` añade exactamente 1. |
| 6.3 | El estado de una sesión nueva lanza error o sale raro | Una sesión sin mensajes no tiene checkpoint | Devuelve `[]`: `agent.get_state(cfg).values.get("messages", [])`. |
| 6.4 | Tras borrar, `get_state` sigue mostrando mensajes | Se borró una variable local o se recreó el checkpointer | Borra en el **mismo** checkpointer con `checkpointer.delete_thread("sesion-alex")` y vuelve a leer con `get_state`. |

## 7. Tests que fallan por mezclar sesiones (reto 03/04)

| # | Síntoma | Causa probable | Solución |
|---|---------|----------------|----------|
| 7.1 | `❌ test_c3_aislamiento_entre_sesiones: A debe ver solo lo suyo` | `guardar_mensaje` ignora `session_id` (hilo fijo o global) | Construye la config con el `session_id` recibido en cada llamada. |
| 7.2 | `❌ test_c4_borrado_independiente` con «B no debe verse afectada» | Se borró el almacén entero o se recreó el grafo | Usa `almacen.checkpointer.delete_thread(session_id)` solo para esa sesión; no llames a `crear_almacen()` dentro de las funciones. |
| 7.3 | `❌ ... Se esperaban 2 mensajes y llegaron 0` | `guardar_mensaje` no llama a `invoke` o devuelve `...` | Completa el TODO 1: `almacen.invoke({"messages": [{"role": rol, "content": contenido}]}, config)`. |
| 7.4 | `❌ El orden debe ser cronológico` | Devolviste los mensajes invertidos | `get_state(...).values["messages"]` ya está en orden cronológico: no lo inviertas. |
| 7.5 | `❌ Primer mensaje incorrecto: {'role': 'human', ...}` | Falta la traducción de roles de LangChain | Devuelve `role` como `"user"`/`"assistant"` (mapeo `human→user`, `ai→assistant`). |
| 7.6 | ⚠️ `TypeError`/`AttributeError` en los tests | La función no devuelve lo esperado | Cada función debe **devolver** (`return`), no solo imprimir. |

## 8. Errores de ejecución en Google Colab

| # | Síntoma | Causa probable | Solución |
|---|---------|----------------|----------|
| 8.1 | `NameError: ... 'userdata'` o import de `google.colab` falla | Estás ejecutando fuera de Colab | No es un error: el notebook detecta el entorno y sigue. Define la variable de entorno si quieres el LLM real. |
| 8.2 | Se reinició el runtime y todo da `NameError` | Colab desconecta el runtime por inactividad o tras instalar | **Runtime → Restart session** y después **Runtime → Run all**. |
| 8.3 | La ejecución se detiene en una celda con error y no avanza | `assert` o excepción sin resolver | Corrige esa celda y vuelve a ejecutar desde ella (*Run current cell and below*) o *Run all* cuando todo pase. |
| 8.4 | `UnicodeEncodeError: 'charmap' codec can't encode ...` al imprimir | Consola local Windows con cp1252 (no ocurre en Colab) | Ejecuta con `python -X utf8` o `$env:PYTHONIOENCODING='utf-8'`; en Colab no aparece. |
| 8.5 | `pip install` falla por red / `Read timed out` | Conexión inestable | Repite la celda de instalación; verifica con `pip show langchain`. |
| 8.6 | El PDF o el PPTX no se abre desde Colab | Colab no gestiona archivos locales del repositorio | Descarga el archivo desde GitHub (botón *Download raw file*) y ábrelo localmente. |

---

**Si aparece un error no listado:** anota el mensaje completo, comprueba con `pip show langchain langgraph langchain-core` qué versiones hay realmente instaladas y consulta la guía de memoria vigente: <https://docs.langchain.com/oss/python/langchain/short-term-memory>
