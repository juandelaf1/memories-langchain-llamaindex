"""Memories — clase en vivo (app Streamlit).

Recorrido A (por defecto): sin API keys; la memoria es la de LangGraph real y
el texto lo genera un modelo determinista simulado.
Recorrido B (opcional): si existe GROQ_API_KEY, se usa el LLM real de Groq.

Uso:  streamlit run app.py
"""

import base64
import os
import uuid
from pathlib import Path

import streamlit as st
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from langgraph.checkpoint.memory import InMemorySaver

ROOT = Path(__file__).resolve().parent

st.set_page_config(
    page_title="Memories — clase en vivo",
    page_icon="🧠",
    layout="wide",
)

SYSTEM_PROMPT = (
    "Eres el asistente de una píldora formativa. Responde SIEMPRE en español, "
    "en menos de 60 palabras y con explicaciones sencillas."
)


# ---------------------------------------------------------------- modelos


class ModeloDeterminista(BaseChatModel):
    """Modelo simulado SIN API: responde según el historial que recibe.

    Solo sustituye la generación del texto. El guardado, la recuperación,
    el aislamiento y el borrado los sigue haciendo LangChain/LangGraph.
    """

    @property
    def _llm_type(self):
        return "modelo-determinista"

    def _generate(self, messages, stop=None, run_manager=None, **kwargs):
        historial = "\n".join(str(m.content) for m in messages)
        ultimo_usuario = ""
        for m in reversed(messages):
            if m.type == "human":
                ultimo_usuario = str(m.content)
                break

        con_contexto = ("Alex" in historial) and ("Python" in historial)

        if "CSV" in ultimo_usuario.upper():
            if con_contexto:
                respuesta = ("Hola Alex, como trabajas con Python y prefieres las explicaciones "
                             "sencillas: pandas.read_csv('fichero.csv') y listo.")
            else:
                respuesta = "Puedes usar pandas.read_csv('fichero.csv')."
        elif "Me llamo" in ultimo_usuario or "Alex" in ultimo_usuario:
            respuesta = "Encantado, Alex. Anotado: Python y explicaciones sencillas."
        else:
            respuesta = "No tengo contexto previo de esta conversacion."

        return ChatResult(generations=[ChatGeneration(message=AIMessage(content=respuesta))])


@st.cache_resource
def get_almacen():
    """Un único almacén en RAM para toda la app (persiste entre reruns)."""
    return InMemorySaver()


@st.cache_resource
def get_agente():
    """Agente con memoria. Con GROQ_API_KEY -> LLM real; sin ella -> determinista."""
    from langchain.agents import create_agent

    if os.environ.get("GROQ_API_KEY"):
        modelo = "groq:openai/gpt-oss-120b"
        etiqueta = "Groq openai/gpt-oss-120b (Recorrido B · CON API)"
    else:
        modelo = ModeloDeterminista()
        etiqueta = "ModeloDeterminista simulado (Recorrido A · SIN API)"

    agente = create_agent(
        model=modelo,
        tools=[],
        system_prompt=SYSTEM_PROMPT,
        checkpointer=get_almacen(),
    )
    return agente, etiqueta


def hilo(id_sesion):
    """Configuración que identifica la conversación ante LangGraph."""
    return {"configurable": {"thread_id": id_sesion}}


def mensajes_de(id_sesion):
    estado = get_agente()[0].get_state(hilo(id_sesion))
    return estado.values.get("messages", [])


def rol_de(m):
    return "user" if m.type == "human" else "assistant"


# ---------------------------------------------------------------- estado de la app

if "sesiones" not in st.session_state:
    st.session_state.sesiones = ["sesion-demo", "sesion-aislada"]

# ---------------------------------------------------------------- cabecera

_logo_b64 = base64.b64encode((ROOT / "assets" / "logo.svg").read_bytes()).decode()
st.markdown(
    f"""
    <div style="display:flex;align-items:center;gap:16px;margin-bottom:4px">
      <img src="data:image/svg+xml;base64,{_logo_b64}" width="64" alt="Logo Memories">
      <div>
        <h1 style="margin:0">Memories — clase en vivo</h1>
        <p style="margin:0;color:#666">Orquestación de flujos con LangChain/LlamaIndex ·
        la memoria se ve, se aísla y se borra</p>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

agente, etiqueta_modelo = get_agente()
st.info(f"**Modelo actual:** {etiqueta_modelo} — la memoria (checkpointer + thread_id) es real en ambos casos.")

# ---------------------------------------------------------------- barra lateral

st.sidebar.header("🎛️ Sesiones (thread_id)")

# El estado del selector vive en st.session_state["sesion_widget"]: los botones
# lo escriben ANTES de instanciar el selectbox, que así queda sincronizado.
if st.sidebar.button("➕ Nueva sesión", use_container_width=True):
    nueva = "sesion-" + uuid.uuid4().hex[:6]
    st.session_state.sesiones.append(nueva)
    st.session_state.sesion_widget = nueva

if st.sidebar.button("🗑️ Borrar sesión activa", type="primary", use_container_width=True):
    actual = st.session_state.get("sesion_widget", st.session_state.sesiones[0])
    get_almacen().delete_thread(actual)          # derecho al borrado, un solo hilo
    st.session_state.sesiones.remove(actual)
    if not st.session_state.sesiones:
        st.session_state.sesiones = ["sesion-" + uuid.uuid4().hex[:6]]
    st.session_state.sesion_widget = st.session_state.sesiones[0]

if st.session_state.get("sesion_widget") not in st.session_state.sesiones:
    st.session_state.sesion_widget = st.session_state.sesiones[0]

activo = st.sidebar.selectbox(
    "Sesión activa",
    st.session_state.sesiones,
    key="sesion_widget",
)

st.sidebar.divider()
with st.sidebar.expander("🗂️ Mapa del almacén"):
    for sid in st.session_state.sesiones:
        n = len(mensajes_de(sid))
        marcador = " ← activa" if sid == st.session_state.sesion_widget else ""
        st.markdown(f"`{sid}`{marcador} — **{n}** mensajes {'█' * n}")

st.sidebar.caption(
    "Cada sesión tiene su propio `thread_id`: cambiar de sesión en el selector "
    "es cambiar de hilo aislado. Borrar una no toca a las demás."
)

# ---------------------------------------------------------------- pestañas

tab_demo, tab_reto, tab_material = st.tabs(
    ["💬 Demo en vivo", "🏁 Reto (sin API)", "📚 Material de la clase"]
)

# -------- pestaña 1: demo con memoria

with tab_demo:
    st.markdown(
        "Escribe algo y observa cómo el historial **se guarda solo**: en una sesión nueva "
        "no hay contexto; en esta, todo lo anterior se reenvía al modelo en cada turno."
    )

    mensajes = mensajes_de(activo)
    if not mensajes:
        st.caption("Sesión vacía: el historial de este `thread_id` empieza de cero.")

    for m in mensajes:
        with st.chat_message(rol_de(m)):
            st.markdown(str(m.content))

    prompt = st.chat_input(f"Hablar con la memoria de '{activo}'…")
    if prompt:
        with st.chat_message("user"):
            st.markdown(prompt)
        with st.chat_message("assistant"):
            with st.spinner("Pensando…"):
                resp = agente.invoke(
                    {"messages": [{"role": "user", "content": prompt}]},
                    hilo(activo),
                )
            st.markdown(resp["messages"][-1].content)

    with st.expander("🔬 Inspeccionar el estado del hilo (get_state)"):
        if mensajes:
            for i, m in enumerate(mensajes):
                st.code(f"[{i}] {m.type}: {m.content}", language=None)
        else:
            st.code("{}", language=None)

# -------- pestaña 2: reto

with tab_reto:
    st.markdown(
        "El reto completo vive en el notebook (misma corrección automática que en clase):\n\n"
        "- **Alumnado:** [03_Reto_Memories_Alumno.ipynb]"
        "(https://colab.research.google.com/github/juandelaf1/memories-langchain-llamaindex/blob/main/notebooks/03_Reto_Memories_Alumno.ipynb)\n"
        "- **Solucionario:** [04_Reto_Memories_Solucion.ipynb]"
        "(https://colab.research.google.com/github/juandelaf1/memories-langchain-llamaindex/blob/main/notebooks/04_Reto_Memories_Solucion.ipynb)\n\n"
        "Implementa tres funciones sobre un `checkpointer` **sin LLM** y supera 4 pruebas:"
    )
    st.markdown(
        """
| # | Función | Qué comprueba el test |
|---|---------|----------------------|
| 1 | `guardar_mensaje(almacen, session_id, rol, contenido)` | El mensaje queda en el hilo correcto |
| 2 | `obtener_historial(almacen, session_id)` | Devuelve la lista con roles `user`/`assistant` |
| 3 | `borrar_sesion(almacen, session_id)` | Borra solo ese hilo; los demás quedan intactos |
| 4 | aislamiento | Dos `session_id` nunca mezclan historiales |
"""
    )
    st.caption("Rúbrica completa: docs/rubrica.md · 4 tests = 4 criterios, sin corrección manual.")

# -------- pestaña 3: material

with tab_material:
    c1, c2 = st.columns(2)
    with c1:
        st.download_button(
            "⬇️ Descargar presentación (PDF)",
            data=(ROOT / "slides" / "01_Memories.pdf").read_bytes(),
            file_name="01_Memories.pdf",
            mime="application/pdf",
            use_container_width=True,
        )
    with c2:
        st.download_button(
            "⬇️ Descargar presentación (PPTX, editable)",
            data=(ROOT / "slides" / "01_Memories.pptx").read_bytes(),
            file_name="01_Memories.pptx",
            mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
            use_container_width=True,
        )

    st.markdown(
        """
**Documentación de la píldora**

- Plan de clase minutado → `docs/plan_de_clase.md`
- Rúbrica (4 criterios) → `docs/rubrica.md`
- Criterio ético → `docs/criterio_etico.md`
- Errores frecuentes → `docs/troubleshooting.md`
- Instrucciones y enlaces de Colab → `README.md`

**Doc oficial**

- [Memoria en LangChain](https://docs.langchain.com/oss/python/concepts/memory)
- [Memoria a corto plazo](https://docs.langchain.com/oss/python/langchain/short-term-memory)
- [Memory en LlamaIndex](https://developers.llamaindex.ai/python/examples/memory/memory/)
"""
    )
