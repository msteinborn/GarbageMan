# RAG Service

Standalone RAG (Retrieval Augmented Generation) service for business terms retrieval.

## Setup

```bash
cd rag_service
uv sync
```

## Run

```bash
uv run main.py
```

## Query Examples

- "What is ROI?"
- "Explain cash flow"
- "Tell me about profitability"

## Features

- Semantic search via embeddings
- Local vector database (Chroma)
- Fallback business glossary dataset
- Zero external API dependencies
