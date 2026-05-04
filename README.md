# 📚 Local Wikipedia RAG Assistant

A fully local ChatGPT-style system that answers questions about **famous people** and **famous places** using Wikipedia data, local embeddings, a local vector database, and a local LLM. No external API calls — everything runs on your machine.

---

## 📋 Table of Contents

1. [Project Overview](#project-overview)
2. [Architecture](#architecture)
3. [Requirements](#requirements)
4. [Installation](#installation)
5. [Ollama Setup](#ollama-setup)
6. [Data Ingestion](#data-ingestion)
7. [Running the App](#running-the-app)
8. [CLI Interface](#cli-interface)
9. [Example Questions](#example-questions)
10. [Query Classification](#query-classification)
11. [Chunking Strategy](#chunking-strategy)
12. [Vector Store Design](#vector-store-design)
13. [Failure Cases](#failure-cases)
14. [Limitations](#limitations)
15. [Possible Improvements](#possible-improvements)
16. [Demo Video](#demo-video)

---

## Project Overview

This project implements a **Retrieval-Augmented Generation (RAG)** system that:

1. **Ingests** Wikipedia articles for 20 famous people and 20 famous places
2. **Chunks** articles into overlapping segments for semantic search
3. **Embeds** chunks using a local embedding model (`nomic-embed-text`)
4. **Stores** embeddings in ChromaDB with rich metadata
5. **Retrieves** relevant context based on classified user queries
6. **Generates** grounded answers using a local LLM (`llama3.2:3b`)
7. **Presents** a chat-style UI via Streamlit (or CLI fallback)

The system is designed to answer only from retrieved context and will say "I don't know" when information is not available.

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                   User Interface                     │
│            (Streamlit Chat / CLI)                     │
└──────────────────┬──────────────────────────────────┘
                   │ user query
                   ▼
┌──────────────────────────────────────────────────────┐
│              Query Classification                     │
│    (rule-based: person / place / both / unknown)      │
└──────────────────┬───────────────────────────────────┘
                   │ classified query
                   ▼
┌──────────────────────────────────────────────────────┐
│              Retrieval (ChromaDB)                      │
│   • Embed query via nomic-embed-text                  │
│   • Semantic search with metadata filtering           │
│   • Return top-k relevant chunks                      │
└──────────────────┬───────────────────────────────────┘
                   │ retrieved context
                   ▼
┌──────────────────────────────────────────────────────┐
│              Generation (Ollama LLM)                  │
│   • Grounded prompt with context                      │
│   • llama3.2:3b / phi3 / mistral                      │
│   • "I don't know" for missing info                   │
└──────────────────┬───────────────────────────────────┘
                   │ answer
                   ▼
┌──────────────────────────────────────────────────────┐
│              Response Display                         │
│   • Streamed answer                                   │
│   • Retrieved context (expandable)                    │
│   • Source URLs                                       │
└──────────────────────────────────────────────────────┘
```

### Data Flow (Ingestion)

```
Wikipedia Pages → Fetch (requests + BeautifulSoup) → Raw JSON (data/raw/)
    → Chunking (500 words, 100 overlap) → Processed JSON (data/processed/)
    → Embedding (nomic-embed-text) → ChromaDB (chroma_db/)
```

---

## Requirements

- **Python** 3.10+
- **Ollama** installed and running locally
- ~4 GB disk space for models
- ~2 GB RAM minimum (more recommended for 3B+ models)

### Python Dependencies

```
requests>=2.31.0
beautifulsoup4>=4.12.0
chromadb>=0.4.0
streamlit>=1.30.0
ollama>=0.1.0
```

---

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/tahacali/Local-Wikipedia-RAG-Assistant.git
cd Local-Wikipedia-RAG-Assistant
```

### 2. Create a Virtual Environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

---

## Ollama Setup

### 1. Install Ollama

Download from [ollama.com](https://ollama.com/) and install for your OS.

### 2. Pull the Required Models

```bash
# Embedding model (required)
ollama pull nomic-embed-text

# LLM model (required — choose one)
ollama pull llama3.2:3b        # Recommended: good balance of quality and speed

# Alternative LLM options:
# ollama pull phi3              # Smaller, faster
# ollama pull mistral           # Larger, higher quality
```

### 3. Verify Ollama is Running

```bash
ollama list
```

You should see `nomic-embed-text` and `llama3.2:3b` (or your chosen model) listed.

---

## Data Ingestion

Run the ingestion pipeline to fetch Wikipedia articles, chunk them, embed them, and store in ChromaDB:

```bash
python scripts/ingest_data.py
```

This will:
1. Check that the embedding model is available
2. Fetch 40 Wikipedia articles (20 people + 20 places)
3. Split each article into ~500-word chunks with 100-word overlap
4. Generate embeddings using `nomic-embed-text`
5. Store everything in ChromaDB at `chroma_db/`

**Expected output:**
```
[1/5] Checking prerequisites...
  ✅ Embedding model available
[2/5] Ingesting 40 Wikipedia articles...
  [FETCH] Albert Einstein from https://en.wikipedia.org/wiki/Albert_Einstein
  [OK]   Albert Einstein — 45231 characters
  ...
[3/5] Chunking 40 articles...
  Albert Einstein: 15 chunks
  ...
[4/5] Embedding and storing 487 chunks in ChromaDB...
  ✅ Stored 487 chunks in 142.3s
[5/5] Final statistics:
  Total chunks in store: 487
  Total entities: 40
```

**To reset and re-ingest:**
```bash
python scripts/reset_store.py          # Reset vector store only
python scripts/reset_store.py --all    # Reset everything (re-fetch from Wikipedia)
```

---

## Running the App

### Streamlit (Recommended)

```bash
streamlit run src/app.py
```

The app will open at `http://localhost:8501` with:
- 💬 Chat-style interface for asking questions
- 📎 Expandable retrieved context for each answer
- ⚙️ Sidebar with system info, retrieval settings, and indexed entities
- 🗑️ Clear chat button

### CLI Interface

```bash
python src/cli.py
```

Commands:
- Type a question to get an answer
- `stats` — Show vector store statistics
- `clear` — Clear the screen
- `quit` — Exit

---

## Example Questions

### People
| Question | Expected Behavior |
|----------|-------------------|
| Who was Albert Einstein and what is he known for? | Answers from Einstein's Wikipedia article |
| What did Marie Curie discover? | Discusses radioactivity, polonium, radium |
| Why is Nikola Tesla famous? | Describes his contributions to electricity |
| Compare Lionel Messi and Cristiano Ronaldo | Uses context from both articles |
| What is Frida Kahlo known for? | Discusses her art and life |

### Places
| Question | Expected Behavior |
|----------|-------------------|
| Where is the Eiffel Tower located? | Paris, France |
| Why is the Great Wall of China important? | Historical and cultural significance |
| What is Machu Picchu? | Incan citadel in Peru |
| What was the Colosseum used for? | Gladiatorial contests, public spectacles |
| Where is Mount Everest? | Nepal/Tibet border, highest peak |

### Mixed / Cross-type
| Question | Expected Behavior |
|----------|-------------------|
| Which famous place is located in Turkey? | Should find Hagia Sophia |
| Which person is associated with electricity? | Should find Tesla (and possibly Einstein) |
| Compare Albert Einstein and Nikola Tesla | Retrieves context from both |
| Compare the Eiffel Tower and the Statue of Liberty | Retrieves context from both |

---

## Query Classification

The system classifies each query into one of four types:

| Type | Description | Filter Applied |
|------|-------------|----------------|
| `person` | Query is about a person | Only person chunks searched |
| `place` | Query is about a place | Only place chunks searched |
| `both` | Query involves both types | All chunks searched |
| `unknown` | Cannot determine type | All chunks searched (fallback) |

**Method:** Rule-based keyword matching against curated keyword lists including:
- Generic keywords (e.g., "who", "born" → person; "where", "located" → place)
- Entity name fragments (e.g., "einstein" → person; "eiffel" → place)

This approach is simple, transparent, and works well for the domain. More sophisticated classification (e.g., using the LLM itself) could be added as an improvement.

---

## Chunking Strategy

**Method:** Fixed-size word-based chunking with overlap

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| Chunk size | 500 words | Large enough for meaningful context, small enough for focused retrieval |
| Overlap | 100 words | Prevents information loss at chunk boundaries |
| Unit | Words | More semantic than character-based splitting |

**Why this approach?**
- Wikipedia articles can be 5,000–50,000+ words long
- 500-word chunks typically contain 1–2 complete paragraphs
- 100-word overlap ensures sentences split across boundaries are captured
- Simple implementation that's easy to understand and debug

---

## Vector Store Design

**Design Choice:** Single ChromaDB collection with metadata filtering (Option B)

### Why One Store?

| Factor | One Store (chosen) | Two Stores |
|--------|-------------------|------------|
| Cross-type queries | Natural, no merging needed | Requires querying both and merging |
| Maintenance | Single collection to manage | Two collections to keep in sync |
| Metadata filtering | ChromaDB supports this efficiently | Not needed (separate stores) |
| Flexibility | Easy to add new entity types | Requires new store per type |

### Metadata Schema

Each chunk in ChromaDB stores:

```json
{
    "entity_name": "Albert Einstein",
    "entity_type": "person",
    "source_url": "https://en.wikipedia.org/wiki/Albert_Einstein",
    "chunk_index": 0,
    "total_chunks": 15
}
```

This enables:
- Filtering by `entity_type` for targeted retrieval
- Tracking provenance via `source_url`
- Understanding chunk position via `chunk_index` / `total_chunks`

---

## Failure Cases

The system handles questions outside its knowledge base:

| Question | Expected Response |
|----------|-------------------|
| Who is the president of Mars? | "I don't know based on the available data." |
| Tell me about John Doe | "I don't know based on the available data." |
| What is quantum teleportation? | May attempt an answer from tangentially related context, or say it doesn't know |

The LLM is instructed via system prompt to only answer from provided context and explicitly say "I don't know" when information is missing.

---

## Limitations

1. **Knowledge scope** — Only knows about the 40 ingested entities
2. **Query classification** — Rule-based; may misclassify novel phrasings
3. **Chunk boundaries** — Important information may span chunk boundaries despite overlap
4. **LLM quality** — 3B parameter model has limited reasoning compared to larger models
5. **No real-time updates** — Wikipedia changes aren't reflected until re-ingestion
6. **Single language** — English only
7. **No conversation memory** — Each question is independent (no multi-turn reasoning)
8. **Retrieval noise** — Top-k results may include irrelevant chunks for ambiguous queries

---

## Possible Improvements

- 🔄 **Conversation memory** — Use chat history for follow-up questions
- 📊 **Re-ranking** — Add a cross-encoder re-ranker for better retrieval precision
- 🌐 **More entities** — Expand beyond 40 to hundreds or thousands
- 🧠 **Better classification** — Use the LLM itself to classify queries
- ⚡ **Caching** — Cache frequent queries and their answers
- 📈 **Latency tracking** — Measure and display retrieval/generation times
- 🔍 **Hybrid search** — Combine semantic search with keyword (BM25) search
- 📝 **Citations** — Highlight which parts of the answer came from which source
- 🤖 **Model comparison** — Let users switch between llama3.2, phi3, mistral in the UI
- 🔀 **Smarter chunking** — Section-aware or paragraph-aware chunking

---

## Demo Video

> **Demo video:** A recorded walkthrough of the system is available upon request.

### Demo Video Script Outline

1. **System Overview** (1 min)
   - Project goal: local Wikipedia RAG
   - Architecture walkthrough
   - Tech stack: Python, Ollama, ChromaDB, Streamlit

2. **Ingestion Demo** (1 min)
   - Run `python scripts/ingest_data.py`
   - Show Wikipedia fetching, chunking, embedding
   - Show stored data in `data/raw/` and `data/processed/`

3. **Question-Answering Demo** (1.5 min)
   - Ask person questions (Einstein, Tesla)
   - Ask place questions (Eiffel Tower, Machu Picchu)
   - Ask mixed questions (compare Einstein and Tesla)
   - Show failure case (president of Mars)

4. **Retrieved Context Explanation** (0.5 min)
   - Expand context panel
   - Show source URLs, similarity scores
   - Explain how context feeds into the LLM prompt

5. **Design Choices & Tradeoffs** (1 min)
   - Single vector store with metadata filtering
   - 500-word chunks with 100-word overlap
   - Rule-based query classification
   - llama3.2:3b model choice
   - Temperature 0.3 for factual answers
   - Limitations and future improvements

---

## Repository Structure

```
Local-Wikipedia-RAG-Assistant/
├── README.md                    # This file
├── Product_prd.md               # Product Requirements Document
├── recommendation.md            # Production deployment recommendations
├── requirements.txt             # Python dependencies
├── .gitignore                   # Git ignore rules
├── data/
│   ├── raw/                     # Raw Wikipedia article JSON files
│   └── processed/               # Chunked article JSON files
├── chroma_db/                   # ChromaDB persistent storage
├── src/
│   ├── __init__.py              # Package init
│   ├── entities.py              # Entity definitions (20 people + 20 places)
│   ├── ingest.py                # Wikipedia scraping and caching
│   ├── chunking.py              # Text chunking with overlap
│   ├── embeddings.py            # Local embedding generation (Ollama)
│   ├── vector_store.py          # ChromaDB operations
│   ├── retrieval.py             # Query classification + retrieval
│   ├── generation.py            # LLM answer generation (Ollama)
│   ├── app.py                   # Streamlit chat UI
│   └── cli.py                   # CLI fallback interface
└── scripts/
    ├── ingest_data.py           # Full ingestion pipeline
    └── reset_store.py           # Reset vector store / data
```
