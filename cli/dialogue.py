from typing import Dict, Any, List, Tuple

from .retrieval import ChunkRetriever

SIMILARITY_THRESHOLD_STRICT = 0.45
SIMILARITY_THRESHOLD_WEAK = 0.25


class CLIDialogueEngine:
	def __init__(self, retriever: ChunkRetriever):
		self.retriever = retriever

	def handle(self, message: str) -> Dict[str, Any]:
		candidates: List[Tuple[str, float]] = self.retriever.search(message, top_k=3)
		if not candidates:
			return {
				"type": "clarify",
				"text": "どのトピックですか？（例：チェックイン、Wi-Fi、駐車場）"
			}
		best_text, best_score = candidates[0]
		if best_score >= SIMILARITY_THRESHOLD_STRICT:
			return {"type": "answer", "text": best_text, "score": best_score}
		if best_score >= SIMILARITY_THRESHOLD_WEAK:
			options = [text.splitlines()[0][:50] for text, _ in candidates]
			return {
				"type": "clarify",
				"text": "こちらのどれですか？",
				"options": options,
				"score": best_score,
			}
		return {
			"type": "escalate",
			"text": "担当者へおつなぎします。",
			"score": best_score,
		}
