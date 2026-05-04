# Product Requirements Document (PRD)
## Local Wikipedia RAG Assistant

## 1. Product Goal

Build a fully local ChatGPT-style system that answers questions about famous people and places using Wikipedia data, local embeddings, ChromaDB, and a local LLM. No external API dependencies.

## 2. Target Users

- University instructors evaluating RAG implementations
- Students learning about retrieval-augmented generation
- Developers prototyping local AI applications

## 3. User Stories

| ID | As a... | I want to... | So that... |
|----|---------|--------------|------------|
| US-1 | User | Ask about famous people | I get Wikipedia-grounded answers |
| US-2 | User | Ask about famous places | I learn about landmarks |
| US-3 | User | See retrieved context | I verify answer sources |
| US-4 | User | Clear chat history | I start fresh |
| US-5 | Evaluator | Run via README only | I assess independently |
| US-6 | Evaluator | See "I don't know" for out-of-scope | I verify hallucination prevention |
| US-7 | User | Compare two entities | I understand differences |
| US-8 | Developer | Reset and re-ingest | I refresh the knowledge base |

## 4. Functional Requirements

### 4.1 Data Ingestion
- Fetch Wikipedia articles for 20+ people and 20+ places
- Include the 10 required people and 10 required places
- Save raw text locally as JSON; support idempotent re-runs
- Handle network errors gracefully

### 4.2 Chunking
- 500-word chunks with 100-word overlap
- Preserve metadata per chunk (entity name, type, URL, chunk index)
- Save processed chunks locally

### 4.3 Embedding & Storage
- Local embeddings via nomic-embed-text (Ollama)
- Single ChromaDB collection with metadata filtering
- Batch embedding; upsert for idempotency

### 4.4 Retrieval
- Classify queries as person/place/both/unknown (rule-based)
- Metadata filtering based on classification
- Return top-k chunks with similarity scores

### 4.5 Generation
- Local LLM (llama3.2:3b) via Ollama
- Grounded answers from context only
- "I don't know" for missing information
- Streaming responses; low temperature (0.3)

### 4.6 User Interface
- Streamlit chat UI with context expanders
- Sidebar with system info and settings
- Clear/reset button; CLI fallback

## 5. Non-Functional Requirements

| ID | Requirement | Target |
|----|------------|--------|
| NFR-1 | Locality | No external API calls |
| NFR-2 | Setup time | < 15 minutes |
| NFR-3 | Response time | < 30 seconds |
| NFR-4 | Reliability | Graceful error handling |
| NFR-5 | Code clarity | Readable Python with comments |
| NFR-6 | Documentation | Complete README, PRD, recommendation |

## 6. System Architecture

```
Data Layer:    Wikipedia → Fetch → Raw JSON → Chunk → Embed → ChromaDB
App Layer:     Query → Classify → Retrieve → Generate → Answer
UI Layer:      Streamlit Chat / CLI
```

| Component | Technology | Purpose |
|-----------|------------|---------|
| Scraper | requests + BeautifulSoup | Fetch Wikipedia |
| Storage | JSON files | Cache raw/processed data |
| Embeddings | Ollama nomic-embed-text | Vector representations |
| Vector DB | ChromaDB | Store and query embeddings |
| Classifier | Rule-based keywords | Route queries |
| LLM | Ollama llama3.2:3b | Generate answers |
| UI | Streamlit / CLI | User interface |

## 7. Data Flow

**Ingestion:** entities.py → fetch Wikipedia → save raw JSON → chunk (500w/100 overlap) → embed → upsert to ChromaDB

**Query:** user question → classify type → embed query → search ChromaDB (filtered) → retrieve top-5 → build prompt → LLM generates → stream answer

## 8. Success Criteria

- All 40 entities ingested successfully
- Correct answers for example questions
- "I don't know" for failure cases
- No external API calls
- Instructor can run from README alone
- Retrieved context is relevant to queries

## 9. Constraints

- No external LLM APIs (OpenAI, Anthropic, Gemini)
- Local execution only
- Must include required 10 people + 10 places
- Language-native code (avoid over-abstraction)
- Must work on consumer hardware

## 10. Risks and Mitigations

| Risk | Mitigation |
|------|------------|
| Ollama not installed | Clear README setup instructions |
| Wikipedia rate limiting | 1s delay, skip-if-cached |
| Slow on CPU | Recommend GPU; note expected times |
| LLM hallucination | Grounded prompt + low temperature |
| Chunk boundary splits | 100-word overlap |
| Ambiguous queries | Default to "both" for max recall |
