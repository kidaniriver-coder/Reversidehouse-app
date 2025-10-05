# Minpaku Guest Chatbot MVP

This MVP provides a Streamlit UI for a PDF-based RAG chatbot, with optional LLM generation.

## Setup

1. Create a virtual environment (recommended)
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. (LLMを使う場合) OpenAI APIキーを設定
   - Windows PowerShell:
     ```powershell
     setx OPENAI_API_KEY "sk-..."
     ```
   - またはプロジェクト直下に `.env` を作成:
     ```ini
     OPENAI_API_KEY=sk-...
     ```

## Streamlit UI

既定の読込先は `./documents`（PDFのみ）。LLM（RAG）を有効化すると、上位チャンクを文脈に生成します。

起動:

```bash
streamlit run main.py
```

LLMが不要な場合は、サイドバーのチェックを外してください。

## CLI (任意)

`documents` 配下の PDF を読み込み、TF-IDF で検索して回答候補を返します。

```bash
python -m cli.app
```
