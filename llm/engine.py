import os
from typing import List, Optional

from dotenv import load_dotenv

load_dotenv()


class LLMEngine:
	def __init__(self, model: str = "gpt-4o-mini"):
		self.model = model
		self.api_key = os.getenv("OPENAI_API_KEY")
		if not self.api_key:
			raise RuntimeError("OPENAI_API_KEY is not set in environment or .env")

		# Try SDK import lazily; fallback to REST if unavailable
		self._sdk_client = None
		try:
			from openai import OpenAI  # type: ignore
			self._sdk_client = OpenAI(api_key=self.api_key)
		except Exception:
			self._sdk_client = None

	def generate(self, question: str, context_chunks: List[str], language: Optional[str] = "ja") -> str:
		context = "\n\n".join(context_chunks[:8]) if context_chunks else ""
		sys_prompt = (
			"あなたは民泊ゲスト対応のコンシェルジュです。"
			"複数の文脈を統合し、矛盾があれば優先度の高い（多数の文脈で一致する）数値や記述を採用してください。"
			"不一致が大きい場合は最も信頼できる候補と代替案を併記し、出典ファイル名(`[FILE:...]`)を括弧で示してください。"
		)
		user_content = (
			f"質問:\n{question}\n\n"
			f"文脈(複数):\n{context}\n\n"
			"出力要件: 1) 要点を最初に1文、2) 具体値、3) 根拠の簡潔な根拠（出典ファイル名）。"
		)

		# Try SDK first
		if self._sdk_client is not None:
			try:
				resp = self._sdk_client.chat.completions.create(
					model=self.model,
					messages=[{"role": "system", "content": sys_prompt}, {"role": "user", "content": user_content}],
					temperature=0.2,
				)
				return resp.choices[0].message.content.strip()
			except Exception:
				pass

		# REST fallback using requests
		import requests
		headers = {
			"Authorization": f"Bearer {self.api_key}",
			"Content-Type": "application/json",
		}
		json_payload = {
			"model": self.model,
			"messages": [
				{"role": "system", "content": sys_prompt},
				{"role": "user", "content": user_content},
			],
			"temperature": 0.2,
		}
		r = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=json_payload, timeout=60)
		r.raise_for_status()
		data = r.json()
		return data["choices"][0]["message"]["content"].strip()
