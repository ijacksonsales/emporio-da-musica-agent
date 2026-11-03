"""Chat UI. Run with: streamlit run app/streamlit_app.py"""

from __future__ import annotations

import json

import streamlit as st

from emporio_agent.llm.base import LLMError
from emporio_agent.memory import is_valid_session_id, new_session_id
from emporio_agent.runtime import Runtime, build_runtime

st.set_page_config(page_title="Empório da Música · Atendimento", page_icon="🎸")


@st.cache_resource
def get_runtime() -> Runtime:
    return build_runtime()


try:
    runtime = get_runtime()
except LLMError as exc:
    st.error(f"{exc}\n\nCopie `.env.example` para `.env` e preencha `GEMINI_API_KEY`.")
    st.stop()

# The session id lives in the URL so a customer can come back to the same conversation
# within the retention period (7 days).
session_id = st.query_params.get("session")
if not is_valid_session_id(session_id):
    session_id = new_session_id()
    st.query_params["session"] = session_id

with st.sidebar:
    st.subheader("Empório da Música")
    st.caption("Protótipo de agente de atendimento")
    if st.button("Nova conversa", width="stretch"):
        st.query_params["session"] = new_session_id()
        st.rerun()
    show_tools = st.toggle("Mostrar ferramentas usadas", value=False)
    st.divider()
    st.caption(f"Data de referência: {runtime.settings.reference_date:%d/%m/%Y}")
    st.caption(f"Modelo: {runtime.settings.llm_model}")
    st.caption(f"Histórico guardado por {runtime.settings.history_ttl_days} dias")

st.title("🎸 Empório da Música")
st.caption("Sua música começa aqui. Fale com a Lia, nossa assistente virtual.")

for message in runtime.memory.load_history(session_id, limit=200):
    with st.chat_message("user" if message.role == "user" else "assistant"):
        st.markdown(message.text)

if prompt := st.chat_input("Digite sua mensagem"):
    with st.chat_message("user"):
        st.markdown(prompt)
    with st.chat_message("assistant"):
        with st.spinner("Lia está digitando..."):
            reply = runtime.chat(session_id, prompt)
        st.markdown(reply.text)
        if show_tools and reply.tool_trace:
            with st.expander(f"Ferramentas usadas ({len(reply.tool_trace)})"):
                for item in reply.tool_trace:
                    st.markdown(f"**{item.call.name}** `{json.dumps(item.call.args, ensure_ascii=False)}`")
                    st.json(item.result, expanded=False)
        if reply.error:
            st.caption(f"Erro técnico: {reply.error}")
