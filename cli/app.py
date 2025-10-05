import os
from typing import Optional

from .loader import load_documents_to_chunks
from .retrieval import ChunkRetriever
from .dialogue import CLIDialogueEngine


def main(documents_dir: Optional[str] = None) -> None:
	project_root = os.path.dirname(os.path.dirname(__file__))
	documents_path = documents_dir or os.path.join(project_root, "documents")
	chunks = load_documents_to_chunks(documents_path)
	if not chunks:
		print("[WARN] documentsに読み込めるPDFが見つかりませんでした: ", documents_path)
	retriever = ChunkRetriever(chunks)
	engine = CLIDialogueEngine(retriever)

	print("Minpaku Chatbot CLI - 質問を入力してください（終了: exit/quit）")
	while True:
		try:
			user = input("> ").strip()
			if user.lower() in {"exit", "quit"}:
				print("終了します。")
				break
			if not user:
				continue
			resp = engine.handle(user)
			type_ = resp.get("type")
			text = resp.get("text")
			print(f"[{type_}] {text}")
			options = resp.get("options")
			if options:
				for i, opt in enumerate(options, 1):
					print(f"  {i}. {opt}")
		except KeyboardInterrupt:
			print("\n中断します。")
			break


if __name__ == "__main__":
	main()
