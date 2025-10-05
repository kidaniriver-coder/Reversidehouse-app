import os
from typing import List, Tuple

from pypdf import PdfReader

try:
	import fitz  # PyMuPDF
	HAVE_MUPDF = True
except Exception:
	HAVE_MUPDF = False


def _extract_with_mupdf(path: str) -> str:
	if not HAVE_MUPDF:
		return ""
	try:
		doc = fitz.open(path)
		texts = []
		for page in doc:
			texts.append(page.get_text("text") or "")
		return "\n".join(texts)
	except Exception:
		return ""


def _extract_with_pypdf(path: str) -> str:
	try:
		reader = PdfReader(path)
		pages_text = []
		for page in reader.pages:
			pages_text.append(page.extract_text() or "")
		return "\n".join(pages_text)
	except Exception:
		return ""


def _read_txt_files(root_dir: str) -> List[Tuple[str, str]]:
	pairs: List[Tuple[str, str]] = []
	for dirpath, _, filenames in os.walk(root_dir):
		for filename in sorted(filenames):
			if filename.lower().endswith(".txt"):
				path = os.path.join(dirpath, filename)
				# Try multiple encodings for robustness on Windows
				content = None
				for enc in ("utf-8", "cp932"):
					try:
						with open(path, "r", encoding=enc) as f:
							content = f.read()
						break
					except Exception:
						continue
				if content is None:
					try:
						with open(path, "r", encoding="utf-8", errors="ignore") as f:
							content = f.read()
					except Exception:
						content = None
				if content:
					pairs.append((filename, content))
	return pairs


def read_pdf_files(root_dir: str) -> List[str]:
	texts: List[str] = []
	for dirpath, _, filenames in os.walk(root_dir):
		for filename in sorted(filenames):
			if filename.lower().endswith(".pdf"):
				path = os.path.join(dirpath, filename)
				text = _extract_with_mupdf(path)
				if not text.strip():
					text = _extract_with_pypdf(path)
				if text.strip():
					# Prepend filename for provenance and retrieval diversity
					header = f"[FILE:{filename}]\n"
					texts.append(header + text)
	return texts


def read_texts_with_names(root_dir: str) -> List[Tuple[str, str]]:
	pairs = _read_txt_files(root_dir)
	if pairs:
		return pairs
	pdf_pairs: List[Tuple[str, str]] = []
	for dirpath, _, filenames in os.walk(root_dir):
		for filename in sorted(filenames):
			if filename.lower().endswith(".pdf"):
				path = os.path.join(dirpath, filename)
				text = _extract_with_mupdf(path)
				if not text.strip():
					text = _extract_with_pypdf(path)
				if text.strip():
					pdf_pairs.append((filename, text))
	return pdf_pairs


def split_into_chunks(text: str, max_chars: int = 800) -> List[str]:
	chunks: List[str] = []
	buffer: List[str] = []
	length = 0
	for line in text.splitlines():
		if not line.strip():
			continue
		if length + len(line) + 1 > max_chars and buffer:
			chunks.append("\n".join(buffer))
			buffer = []
			length = 0
		buffer.append(line)
		length += len(line) + 1
	if buffer:
		chunks.append("\n".join(buffer))
	return chunks


def load_documents_to_chunks(documents_dir: str) -> List[str]:
	all_chunks: List[str] = []
	texts = read_pdf_files(documents_dir)
	for t in texts:
		all_chunks.extend(split_into_chunks(t))
	# If there are TXT files, include them as well (preferred when present)
	txt_pairs = _read_txt_files(documents_dir)
	for fname, text in txt_pairs:
		prefixed = f"[FILE:{fname}]\n" + text
		all_chunks.extend(split_into_chunks(prefixed))
	return all_chunks
