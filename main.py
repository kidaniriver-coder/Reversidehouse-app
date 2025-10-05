import os
import streamlit as st

from cli.loader import load_documents_to_chunks, read_texts_with_names
from cli.retrieval import ChunkRetriever
from cli.dialogue import CLIDialogueEngine

# Optional LLM
LLM_AVAILABLE = True
try:
	from llm.engine import LLMEngine
except Exception:
	LLM_AVAILABLE = False

st.set_page_config(page_title="Minpaku Chatbot", page_icon="🏠", layout="centered")

st.title("民泊ゲスト向けチャットボット (MVP)")

# Sidebar: data source + options
project_root = os.path.dirname(__file__)
default_documents = os.path.join(project_root, "documents")

doc_dir = st.sidebar.text_input("PDFフォルダ (documents)", value=default_documents)
use_llm = st.sidebar.checkbox("LLMで回答生成する (RAG)", value=LLM_AVAILABLE, disabled=not LLM_AVAILABLE)
model_name = st.sidebar.text_input("OpenAIモデル", value="gpt-4o-mini", disabled=not use_llm)
reload_clicked = st.sidebar.button("ドキュメント再読込")

with st.expander("診断情報"):
	try:
		import httpx  # type: ignore
		import openai  # type: ignore
		st.write({"httpx": getattr(httpx, "__version__", "unknown"), "openai": getattr(openai, "__version__", "unknown")})
	except Exception as e:
		st.write({"error": str(e)})
	st.write({"LLM_AVAILABLE": LLM_AVAILABLE})
	if "chunks" in st.session_state:
		st.write({"chunks": len(st.session_state.get("chunks", []))})
		st.write({"files": st.session_state.get("loaded_files", [])})

if "retriever" not in st.session_state or reload_clicked or st.session_state.get("doc_dir") != doc_dir:
	# Load corpus (TXT優先、なければPDF)
	chunks = load_documents_to_chunks(doc_dir)
	texts_with_names = read_texts_with_names(doc_dir)
	st.session_state.loaded_files = [name for name, _ in texts_with_names]

	st.session_state.doc_dir = doc_dir
	st.session_state.chunks = chunks
	st.session_state.retriever = ChunkRetriever(chunks)
	st.session_state.engine = CLIDialogueEngine(st.session_state.retriever)
	st.session_state.messages = []
	if not chunks:
		st.info("documents内のTXTまたはPDFが見つからないか、抽出できませんでした。フォルダパスと文字コードを確認し、再読込してください。")

if use_llm and LLM_AVAILABLE:
	try:
		st.session_state.llm = LLMEngine(model=model_name)
	except Exception as e:
		st.warning(f"LLM初期化に失敗しました: {e}")
		st.session_state.llm = None
else:
	st.session_state.llm = None

# Chat history
if "messages" not in st.session_state:
	st.session_state.messages = []

for m in st.session_state.messages:
	with st.chat_message(m["role"]):
		st.markdown(m["content"])

user_input = st.chat_input("ご質問を入力してください")
if user_input:
	st.session_state.messages.append({"role": "user", "content": user_input})
	with st.chat_message("user"):
		st.markdown(user_input)

	assistant_text = ""
	if st.session_state.llm is not None:
		retrieved = st.session_state.retriever.search(user_input, top_k=5)
		context_chunks = [text for text, _ in retrieved]
		try:
			assistant_text = st.session_state.llm.generate(user_input, context_chunks)
		except Exception as e:
			assistant_text = f"LLM呼び出しでエラーが発生しました: {e}"
	else:
		decision = st.session_state.engine.handle(user_input)
		assistant_text = decision.get("text") or "回答を生成できませんでした。"
		options = decision.get("options")
		if options:
			assistant_text += "\n\n候補:\n" + "\n".join([f"- {o}" for o in options])

	with st.chat_message("assistant"):
		st.markdown(assistant_text)
	st.session_state.messages.append({"role": "assistant", "content": assistant_text})
