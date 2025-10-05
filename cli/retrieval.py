from typing import List, Tuple, Dict

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def _extract_filename_prefix(text: str) -> str:
	if text.startswith("[FILE:"):
		end = text.find("]")
		if end != -1:
			return text[6:end]
	return ""


class ChunkRetriever:
	def __init__(self, chunks: List[str]):
		self.chunks = chunks
		# Use character n-grams for Japanese/multilingual text
		self.vectorizer = TfidfVectorizer(
			analyzer='char',
			ngram_range=(3, 5),
			min_df=1,
			max_features=None,
		)
		self.matrix = self.vectorizer.fit_transform(self.chunks) if self.chunks else None

	def search(self, query: str, top_k: int = 8, per_file_limit: int = 2) -> List[Tuple[str, float]]:
		if not query or not self.chunks or self.matrix is None:
			return []
		query_vec = self.vectorizer.transform([query])
		scores = cosine_similarity(query_vec, self.matrix).flatten()
		indexed = list(enumerate(scores))
		indexed.sort(key=lambda x: x[1], reverse=True)

		results: List[Tuple[str, float]] = []
		per_file_count: Dict[str, int] = {}
		for idx, score in indexed:
			chunk = self.chunks[idx]
			fname = _extract_filename_prefix(chunk)
			count = per_file_count.get(fname, 0)
			if count >= per_file_limit:
				continue
			results.append((chunk, float(score)))
			per_file_count[fname] = count + 1
			if len(results) >= top_k:
				break
		return results
