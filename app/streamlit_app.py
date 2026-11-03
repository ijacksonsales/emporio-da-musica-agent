"""Chat UI. Run with: streamlit run app/streamlit_app.py"""

from __future__ import annotations

import json
import re
import time

import streamlit as st

from emporio_agent.llm.base import LLMError
from emporio_agent.memory import is_valid_session_id, new_session_id
from emporio_agent.runtime import Runtime, build_runtime

st.set_page_config(page_title="Empório da Música · Atendimento", page_icon="🎸")

WORD_DELAY_SECONDS = 0.025


def escape_markdown(text: str) -> str:
    """Streamlit renders text between two '$' as LaTeX, which breaks prices like 'R$ 10'."""
    return text.replace("$", "\\$")


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
    if runtime.settings.llm_fallback_model:
        st.caption(f"Fallback (se a quota acabar): {runtime.settings.llm_fallback_model}")
    st.caption(f"Histórico guardado por {runtime.settings.history_ttl_days} dias")

st.title("🎸 Empório da Música")
st.caption("Sua música começa aqui. Fale com a Lia, nossa assistente virtual.")

for message in runtime.memory.load_history(session_id, limit=200):
    with st.chat_message("user" if message.role == "user" else "assistant"):
        st.markdown(escape_markdown(message.text))

if prompt := st.chat_input("Digite sua mensagem"):
    with st.chat_message("user"):
        st.markdown(escape_markdown(prompt))
    with st.chat_message("assistant"):
        result: dict = {}

        def stream_reply():
            # Streamlit's write_stream consumes plain iterators, so capture the
            # generator's return value (the final AgentReply) here.
            chunks = runtime.chat_stream(session_id, prompt)
            while True:
                try:
                    chunk = next(chunks)
                except StopIteration as done:
                    result["reply"] = done.value
                    return
                # Gemini streams sentence-sized chunks; pace them word by word on screen.
                for word in re.findall(r"\S+\s*|\s+", escape_markdown(chunk)):
                    yield word
                    time.sleep(WORD_DELAY_SECONDS)

        st.write_stream(stream_reply())
        reply = result["reply"]
        if show_tools and reply.tool_trace:
            with st.expander(f"Ferramentas usadas ({len(reply.tool_trace)})"):
                for item in reply.tool_trace:
                    st.markdown(f"**{item.call.name}** `{json.dumps(item.call.args, ensure_ascii=False)}`")
                    st.json(item.result, expanded=False)
        if reply.model and reply.model != runtime.settings.llm_model:
            st.caption(f"Respondido pelo modelo de fallback ({reply.model}): quota do principal esgotada.")
        if reply.error:
            st.caption(f"Erro técnico: {reply.error}")
