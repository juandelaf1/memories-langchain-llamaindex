"""Memories — la clase en vivo (app Streamlit).

Utilidad: DEMO PROYECTABLE de la píldora. El formador (o el alumnado) pulsa los
escenarios y la app explica en pantalla qué está pasando con la memoria. La
actividad de código (reto) sigue siendo el notebook 03; aquí no se duplica.

Recorrido A (por defecto): sin API keys; la memoria es la de LangGraph real y
el texto lo genera un modelo determinista simulado.
Recorrido B (opcional): con GROQ_API_KEY (entorno o secrets de Streamlit),
se usa el LLM real de Groq.

Uso local:      streamlit run app.py
En la nube:     Streamlit Community Cloud apuntando a este app.py del repo.
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
    page_title="Memories — la clase en vivo",
    page_icon="🧠",
    layout="wide",
)

SYSTEM_PROMPT = (
    "Eres el asistente de una píldora formativa. Responde SIEMPRE en español, "
    "en menos de 60 palabras y con explicaciones sencillas."
)

# ====================================================================== CSS

CSS = """
<style>
  .block-container { padding-top: 1.1rem; max-width: 1200px; }
  header[data-testid="stHeader"] { background: rgba(0,0,0,0); }

  .cabecera {
    background: linear-gradient(115deg, #0B1220 0%, #152238 45%, #0F766E 130%);
    border: 1px solid #22314f;
    border-radius: 18px;
    padding: 20px 26px;
    display: flex; gap: 18px; align-items: center;
    margin-bottom: .4rem;
  }
  .cabecera h1 { margin: 0; font-size: 1.85rem; color: #F2F7FF; }
  .cabecera p  { margin: 5px 0 0; color: #9FB3CE; font-size: .95rem; }

  .explicador {
    border-left: 4px solid #2DD4BF;
    background: linear-gradient(90deg, rgba(45,212,191,.10), rgba(21,34,56,.55));
    border-radius: 12px;
    padding: 12px 16px;
    margin: 6px 0 14px 0;
  }
  .explicador .titulo { font-weight: 700; color: #5EEAD4; margin-bottom: 2px; }
  .explicador .cuerpo  { color: #D7E3F4; font-size: .95rem; }

  .nota {
    border: 1px dashed #2b3c5e;
    border-radius: 12px;
    padding: 10px 14px;
    color: #9FB3CE; font-size: .88rem;
  }
  [data-testid="stMetric"] {
    background: #101a2e; border: 1px solid #22314f;
    border-radius: 12px; padding: 8px 12px;
  }
  [data-testid="stMetricValue"] { font-size: 1.5rem; }
  .escenario-btn button { min-height: 64px; white-space: pre-wrap; }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)


# ====================================================================== modelos


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


def _clave_groq():
    """Clave desde el entorno o desde los secrets de Streamlit (Community Cloud)."""
    clave = os.environ.get("GROQ_API_KEY")
    if clave:
        return clave
    try:
        return st.secrets["GROQ_API_KEY"]
    except Exception:
        return None


@st.cache_resource
def get_almacen():
    """Un único almacén en RAM para toda la app (persiste entre reruns)."""
    return InMemorySaver()


@st.cache_resource
def get_agente(con_clave: bool):
    """Agente con memoria. con_clave=True -> Groq real; False -> determinista."""
    from langchain.agents import create_agent

    modelo = "groq:openai/gpt-oss-120b" if con_clave else ModeloDeterminista()

    return create_agent(
        model=modelo,
        tools=[],
        system_prompt=SYSTEM_PROMPT,
        checkpointer=get_almacen(),
    )


def hilo(id_sesion):
    """Configuración que identifica la conversación ante LangGraph."""
    return {"configurable": {"thread_id": id_sesion}}


def mensajes_de(id_sesion):
    estado = get_agente(CON_CLAVE).get_state(hilo(id_sesion))
    return estado.values.get("messages", [])


def n_mensajes(id_sesion):
    return len(mensajes_de(id_sesion))


def invocar(id_sesion, texto):
    return get_agente(CON_CLAVE).invoke(
        {"messages": [{"role": "user", "content": texto}]},
        hilo(id_sesion),
    )


def responder(sesion, pregunta):
    """El agente responde y se registra la sesión en la lista."""
    if sesion not in st.session_state.sesiones:
        st.session_state.sesiones.append(sesion)
    return invocar(sesion, pregunta)


def explicar(titulo, cuerpo):
    st.session_state.explicador = {"titulo": titulo, "cuerpo": cuerpo}


CON_CLAVE = bool(_clave_groq())
MODO = ("Recorrido B · LLM real de Groq" if CON_CLAVE
        else "Recorrido A · modelo determinista simulado (sin API)")

# ====================================================================== estado

if "sesiones" not in st.session_state:
    st.session_state.sesiones = ["sesion-demo"]
if "sesion_widget" not in st.session_state:
    st.session_state.sesion_widget = "sesion-demo"
if "explicador" not in st.session_state:
    st.session_state.explicador = None

# Cambio de sesión pedido por un escenario: se aplica AQUÍ, antes de instanciar
# el selectbox (Streamlit prohíbe escribir su clave una vez renderizado).
if "cambiar_a" in st.session_state:
    destino = st.session_state.pop("cambiar_a")
    if destino in st.session_state.sesiones:
        st.session_state.sesion_widget = destino

# ====================================================================== cabecera

_logo_b64 = base64.b64encode((ROOT / "assets" / "memories.png").read_bytes()).decode()
st.markdown(
    f"""
    <div class="cabecera">
      <img src="data:image/png;base64,{_logo_b64}" width="92"
           style="border-radius:18px;box-shadow:0 6px 24px rgba(0,0,0,.45)" alt="Logo Memories">
      <div>
        <h1>Memories — la clase en vivo</h1>
        <p>Guarda · recupera · aísla · borra — la memoria la construye tu aplicación, no el LLM</p>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

c1, c2, c3, c4 = st.columns([2.2, 1, 1, 1.6])
with c1:
    st.caption(f"**Modo actual:** {MODO} — el checkpointer y el `thread_id` son reales en ambos casos.")
with c2:
    st.metric("Sesiones", len(st.session_state.sesiones))
with c3:
    st.metric("Mensajes guardados", sum(n_mensajes(s) for s in st.session_state.sesiones))
with c4:
    if CON_CLAVE:
        st.success("🟢 Con LLM real (Groq)")
    else:
        st.info("🔵 Sin API — demo determinista")

# ====================================================================== barra lateral

st.sidebar.header("🎛️ Sesiones (thread_id)")

if st.sidebar.button("🔁 Reiniciar la demo", use_container_width=True):
    for sid in ("esc-alex", "esc-otra", *list(st.session_state.sesiones)):
        get_almacen().delete_thread(sid)
    st.session_state.sesiones = ["sesion-demo"]
    st.session_state.sesion_widget = "sesion-demo"
    st.session_state.explicador = None
    st.rerun()

if st.sidebar.button("➕ Nueva sesión vacía", use_container_width=True):
    nueva = "sesion-" + uuid.uuid4().hex[:6]
    st.session_state.sesiones.append(nueva)
    st.session_state.sesion_widget = nueva

if st.sidebar.button("🗑️ Borrar sesión activa", type="primary", use_container_width=True):
    actual = st.session_state.sesion_widget
    get_almacen().delete_thread(actual)
    if actual in st.session_state.sesiones:
        st.session_state.sesiones.remove(actual)
    if not st.session_state.sesiones:
        st.session_state.sesiones = ["sesion-demo"]
    st.session_state.sesion_widget = st.session_state.sesiones[0]
    explicar("Sesión borrada",
             f"`delete_thread(\"{actual}\")` eliminó el checkpoint de ese hilo. "
             "Las demás sesiones no se enteran: el borrado es selectivo.")
    st.rerun()

if st.session_state.sesion_widget not in st.session_state.sesiones:
    st.session_state.sesion_widget = st.session_state.sesiones[0]

activo = st.sidebar.selectbox(
    "Sesión activa (el chat usa esta)",
    st.session_state.sesiones,
    key="sesion_widget",
)

st.sidebar.divider()
st.sidebar.subheader("🗂️ Mapa del almacén")
for sid in st.session_state.sesiones:
    n = n_mensajes(sid)
    marca = " ← **activa**" if sid == st.session_state.sesion_widget else ""
    st.sidebar.markdown(f"`{sid}`{marca}  \n{'🟩' * min(n, 10)}{'⬜' * max(0, 10 - n)} **{n}**")

st.sidebar.caption(
    "Cada fila es un `thread_id`: un historial independiente. "
    "Cambiar de sesión en el selector es cambiar de conversación aislada."
)

# ====================================================================== pestañas

tab_demo, tab_como, tab_clase = st.tabs(
    ["🎬 Demo guiada", "🧠 Cómo funciona", "📋 Para la clase"]
)


# ------------------------------------------------------------------ demo guiada

with tab_demo:
    st.markdown(
        "Pulsa los escenarios **en orden** mientras explicas en voz alta: son los cinco "
        "momentos de la demo de la clase. Debajo tienes el chat libre para jugar."
    )

    esc = st.columns(5, gap="small")
    with esc[0]:
        b1 = st.button("1️⃣\nPresentarme", use_container_width=True, key="e1")
    with esc[1]:
        b2 = st.button("2️⃣\nPreguntar en\nel MISMO hilo", use_container_width=True, key="e2")
    with esc[2]:
        b3 = st.button("3️⃣\nRepetir en OTRA\nsesión", use_container_width=True, key="e3")
    with esc[3]:
        b4 = st.button("4️⃣\nVer el almacén\npor dentro", use_container_width=True, key="e4")
    with esc[4]:
        b5 = st.button("5️⃣\nBorrar la sesión\nde Alex", use_container_width=True, key="e5")

    if b1:
        r = responder("esc-alex", "Me llamo Alex, trabajo con Python y prefiero explicaciones sencillas.")
        st.session_state.cambiar_a = "esc-alex"
        explicar(
            "Escenario 1 · el mensaje se GUARDA",
            f"Tu mensaje viajó al agente con `thread_id = \"esc-alex\"`. El **checkpointer** "
            f"(el almacén de LangGraph) añadió 2 mensajes: el tuyo y la respuesta. "
            f"Ahora ese hilo tiene **{n_mensajes('esc-alex')} mensajes**. "
            "Respuesta del asistente: «*"
            + str(r['messages'][-1].content)[:90]
            + "…*». Nota: el asistente **no guarda nada**; el que guarda es tu aplicación.",
        )
        st.rerun()

    if b2:
        if n_mensajes("esc-alex") == 0:
            explicar("Primero el escenario 1", "Este paso necesita que Alex ya se haya presentado en el escenario 1.")
        else:
            antes = n_mensajes("esc-alex")
            r = responder("esc-alex", "¿Cómo puedo leer un archivo CSV?")
            explicar(
                "Escenario 2 · el historial se REENVÍA",
                f"Se enviaron al modelo los **{antes} mensajes anteriores + tu nueva pregunta** "
                f"(ahora hay {n_mensajes('esc-alex')}). Por eso la respuesta usa el contexto del "
                "escenario 1: el LLM es el mismo de siempre, stateless; lo que cambia es que "
                "**la aplicación le pasó el historial**. Eso es la memoria conversacional.",
            )
        st.rerun()

    if b3:
        r = responder("esc-otra", "¿Cómo puedo leer un archivo CSV?")
        st.session_state.cambiar_a = "esc-otra"
        explicar(
            "Escenario 3 · el AISLAMIENTO por thread_id",
            "Misma pregunta, mismo modelo, **otro `thread_id`** (\"esc-otra\"): la respuesta no "
            "sabe quién es Alex ni que prefiere Python, porque ese historial vive en el hilo "
            "«esc-alex» y aquí no se reenvía nada. "
            "Si dos usuarios compartieran el mismo `thread_id`, Alex contaría su vida al otro: "
            "por eso **un id por sesión**.",
        )
        st.rerun()

    if b4:
        alex = n_mensajes("esc-alex")
        otra = n_mensajes("esc-otra")
        explicar(
            "Escenario 4 · ver el almacén por dentro",
            f"Mira el **mapa del almacén** (barra lateral) y el panel de historial de abajo: "
            f"«esc-alex» tiene {alex} mensajes y «esc-otra» {otra}. "
            "Esos diccionarios/listas es **todo** lo que hay: `agent.get_state(config).values[\"messages\"]`. "
            "No hay magia en el modelo: es estado de la aplicación, inspeccionable y borrable.",
        )
        st.rerun()

    if b5:
        if n_mensajes("esc-alex") == 0:
            explicar("Nada que borrar", "Primero ejecuta el escenario 1 (la sesión de Alex está vacía).")
        else:
            get_almacen().delete_thread("esc-alex")
            explicar(
                "Escenario 5 · el BORRADO (derecho al olvido)",
                f"`delete_thread(\"esc-alex\")` dejó ese hilo en **0 mensajes** y «esc-otra» sigue "
                "intacta. El borrado es una operación técnica de la aplicación, selectiva por hilo: "
                "exactamente lo que exige el RGPD cuando alguien pide eliminar su conversación. "
                "Guarda más no es mejor: minimiza, aísla, borra.",
            )
        st.rerun()

    # ---- explicador persistente
    if st.session_state.explicador:
        e = st.session_state.explicador
        st.markdown(
            f"""
            <div class="explicador">
              <div class="titulo">💡 {e['titulo']}</div>
              <div class="cuerpo">{e['cuerpo']}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # ---- chat libre
    st.divider()
    st.subheader(f"💬 Chat libre — sesión `{activo}`")
    for m in mensajes_de(activo):
        with st.chat_message("user" if m.type == "human" else "assistant"):
            st.markdown(str(m.content))

    prompt = st.chat_input(f"Escribe en '{activo}' y observa cómo crece el hilo…")
    if prompt:
        with st.chat_message("user"):
            st.markdown(prompt)
        with st.chat_message("assistant"):
            with st.spinner("Pensando…"):
                r = invocar(activo, prompt)
            st.markdown(str(r["messages"][-1].content))
        explicar(
            "Chat libre",
            f"Se reenviaron al modelo **{n_mensajes(activo)} mensajes** del hilo "
            f"«{activo}» (historial completo + tu pregunta). El checkpointer guardó la "
            "nueva respuesta: mira cómo sube la barra del mapa del almacén.",
        )
        st.rerun()

    with st.expander("🔬 Estado crudo del hilo activo (get_state)"):
        msj = mensajes_de(activo)
        if not msj:
            st.code("{}  # hilo sin checkpoint: sesión vacía", language="python")
        else:
            for i, m in enumerate(msj):
                st.code(f"[{i:02d}] {m.type}: {m.content}", language=None)
            st.caption(
                "Así lo ve tu código: `agente.get_state(cfg).values[\"messages\"]`. "
                "Los tipos `human`/`ai` de LangChain se traducen a `user`/`assistant` en el reto."
            )


# ------------------------------------------------------------------ cómo funciona

with tab_como:
    st.subheader("El problema: los LLM son *stateless*")
    st.markdown(
        "Cada llamada al modelo empieza de cero: no recuerda la anterior. "
        "Si tu aplicación no guarda el historial y se lo reenvía, no hay continuidad."
    )

    st.subheader("La solución: checkpointer + thread_id")
    st.markdown(
        """
        | Pieza | Papel | Ejemplo |
        |---|---|---|
        | `checkpointer` | **El almacén**: persiste el estado de cada conversación | `InMemorySaver()` (en RAM; en producción, SQLite/Postgres) |
        | `thread_id` | **La etiqueta de la sesión**: separa una conversación de otra | `"sesion-alex"`, `"sesion-nueva"` |

        ```
           Turno n
         ┌───────────────┐
         │    Usuario    │── mensaje ─▶ ┌──────────────────────────────────────────┐
         └───────────────┘              │  HISTORIAL DEL HILO  (thread_id)         │
                                        │  [(user, "Me llamo Alex..."), (ai, ...)] │
              prompt = system           │        ▲                    │            │
              + historial               │        │ respuesta          │ se recupera│
              + mensaje nuevo           │        │ guardada           │ todo       │
         ┌───────────────┐              │        │                    ▼            │
         │      LLM      │◀── resp. ──  │   [ preparar prompt ] ──▶ [ LLM ]        │
         └───────────────┘              └──────────────────────────────────────────┘
                                         checkpointer = el almacén

           Sesión nueva = otro thread_id = historial vacío = sin contexto previo
        ```
        """
    )

    st.subheader("Los tres niveles de memoria")
    st.markdown(
        """
        | Nivel | Qué guarda | En esta píldora |
        |---|---|---|
        | **Historial** | La lista de mensajes de la conversación | `get_state(cfg).values["messages"]` |
        | **Corto plazo** | La sesión completa, hasta que se borra o se cierra | `checkpointer` + `thread_id` |
        | **Persistente** | Entre sesiones (perfil, preferencias) | Diseño aparte: store/base de datos + **consentimiento** |
        """
    )

    st.subheader("LangChain y LlamaIndex: la misma idea")
    st.markdown(
        """
        | | LangChain (visto arriba) | LlamaIndex |
        |---|---|---|
        | Objeto central | `checkpointer` + `thread_id` | clase **`Memory`** con `session_id` |
        | Corto plazo | estado del hilo (checkpoint) | cola FIFO con límite de tokens |
        | Largo plazo | `store` con namespaces | **Memory Blocks** (hechos, estáticos, vectoriales) |

        LlamaIndex **no se instala aquí**: solo situar sus nombres. En ambos frameworks,
        alguien tiene que guardar el historial y reenviarlo: eso es la memoria.
        """
    )

    st.subheader("Límites: guardar más no es mejor")
    st.markdown(
        """
        - El historial crece → **ventana de contexto** y **coste por token** en cada turno.
        - Datos **sensibles o erróneos** se reutilizan después como si fueran ciertos.
        - Un `thread_id` compartido = **fuga de contexto** entre usuarios.
        - La regla práctica: **minimiza, aísla, borra** (criterio ético completo en `docs/criterio_etico.md`).
        """
    )


# ------------------------------------------------------------------ para la clase

with tab_clase:
    st.subheader("Plan de la píldora (60 min)")
    st.markdown(
        """
        | Min | Bloque |
        |---|---|
        | 0–5 | **El problema**: dos preguntas sin memoria → el LLM no recuerda |
        | 5–15 | **Conceptos**: qué es/no es, tres niveles, diagrama (pestaña «Cómo funciona») |
        | 15–30 | **Demo en vivo**: los 5 escenarios de esta app o el notebook 02 |
        | 30–50 | **Reto** en Colab: 3 funciones + 4 tests (notebook 03) |
        | 50–55 | *Run all* conjunto → `4/4` = rúbrica automática |
        | 55–60 | Límites, criterio ético y cierre |
        """
    )

    st.subheader("Notebooks en Google Colab")
    st.markdown(
        """
        | Notebook | Uso | Enlace |
        |---|---|---|
        | Reto | **Alumnado** (sin API, con tests) | [Abrir en Colab](https://colab.research.google.com/github/juandelaf1/memories-langchain-llamaindex/blob/main/notebooks/03_Reto_Memories_Alumno.ipynb) |
        """
    )

    c1, c2 = st.columns(2)
    with c1:
        st.download_button(
            "⬇️ Presentación (PDF de reparto)",
            data=(ROOT / "slides" / "01_Memories.pdf").read_bytes(),
            file_name="01_Memories.pdf",
            mime="application/pdf",
            use_container_width=True,
        )
    with c2:
        st.download_button(
            "⬇️ Presentación (PPTX editable + notas)",
            data=(ROOT / "slides" / "01_Memories.pptx").read_bytes(),
            file_name="01_Memories.pptx",
            mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
            use_container_width=True,
        )

    st.info(
        "Documentación completa del repositorio: `README.md` (recorridos A/B), "
        "`docs/plan_de_clase.md` (guion minutado), `docs/rubrica.md` (4 criterios), "
        "`docs/criterio_etico.md` y `docs/troubleshooting.md`."
    )
