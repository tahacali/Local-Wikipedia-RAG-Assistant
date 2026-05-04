# Production Deployment Recommendations
## Local Wikipedia RAG Assistant

## 1. Production Architecture

For production deployment, the system should evolve from a single-machine setup to a distributed, scalable architecture:

```
                    ┌─────────────┐
                    │   CDN/LB    │
                    └──────┬──────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
        ┌─────▼─────┐ ┌───▼───┐ ┌─────▼─────┐
        │  Web App   │ │  API  │ │  Web App   │
        │ (Replicas) │ │Gateway│ │ (Replicas) │
        └─────┬──────┘ └───┬───┘ └─────┬──────┘
              │            │            │
              └────────────┼────────────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
        ┌─────▼─────┐ ┌───▼────┐ ┌────▼─────┐
        │ Model     │ │ Vector │ │ Cache    │
        │ Serving   │ │   DB   │ │ (Redis)  │
        │ (vLLM)    │ │(Pinecone)│          │
        └───────────┘ └────────┘ └──────────┘
```

## 2. Model Serving Options

| Option | Pros | Cons | Best For |
|--------|------|------|----------|
| **vLLM** | High throughput, GPU batching | Requires GPU servers | High-traffic production |
| **TGI (HuggingFace)** | Easy setup, good docs | Less flexible | Medium scale |
| **Ollama (current)** | Simple, local | Single-user, no batching | Development/demo |
| **TensorRT-LLM** | NVIDIA optimized, fastest | Complex setup | Maximum performance |

**Recommendation:** Use **vLLM** with a 7B–13B model (e.g., Llama 3.1 8B) on GPU instances for production. Serve via HTTP API behind a load balancer.

## 3. Vector Database Options

| Option | Pros | Cons | Best For |
|--------|------|------|----------|
| **Pinecone** | Managed, scalable, fast | Cloud-hosted, cost | SaaS production |
| **Weaviate** | Self-hosted, feature-rich | Operational overhead | Self-managed production |
| **Qdrant** | Fast, good API | Newer ecosystem | Performance-focused |
| **ChromaDB (current)** | Simple, embedded | Not for multi-user | Development/small scale |
| **pgvector** | Uses existing Postgres | Less specialized | Teams with Postgres |

**Recommendation:** Use **Pinecone** or **Qdrant** for managed/self-hosted production. If the team already uses PostgreSQL, **pgvector** is a practical choice.

## 4. Data Refresh Strategy

### Approach: Scheduled Re-ingestion with Change Detection

1. **Scheduled pipeline** — Run ingestion weekly via cron/Airflow
2. **Change detection** — Compare Wikipedia revision IDs to detect updates
3. **Incremental updates** — Only re-embed changed articles
4. **Versioning** — Maintain version metadata for rollback capability

```
Scheduler (Airflow/cron)
    → Check Wikipedia revision IDs
    → Fetch changed articles only
    → Re-chunk and re-embed
    → Upsert to vector DB (atomic swap or versioned collection)
```

### Scaling Data
- Current: 40 entities, ~500 chunks
- Production target: 10,000+ entities, 100,000+ chunks
- Consider pre-built Wikipedia embeddings datasets for bootstrapping

## 5. Monitoring and Logging

### Key Metrics to Track
- **Retrieval quality:** Relevance scores, click-through on context
- **Generation quality:** User feedback (thumbs up/down), answer length
- **Latency:** Embedding time, retrieval time, generation time (P50, P95, P99)
- **Throughput:** Queries per second, concurrent users
- **Errors:** Failed retrievals, LLM timeouts, embedding failures

### Tools
- **Logging:** Structured logging with ELK stack or Datadog
- **Tracing:** OpenTelemetry for end-to-end request tracing
- **Dashboards:** Grafana for real-time metrics
- **Alerts:** PagerDuty/Slack for error rate spikes

### RAG-Specific Monitoring
- Track query classification distribution (person/place/both)
- Monitor retrieval recall — are relevant chunks being returned?
- Log LLM prompts and responses for quality review
- A/B test different chunk sizes, overlap values, and models

## 6. Security and Privacy Considerations

| Concern | Mitigation |
|---------|------------|
| **Data source trust** | Only ingest from Wikipedia (public, CC-licensed) |
| **Prompt injection** | Sanitize user inputs; limit prompt length |
| **Model output safety** | Content filtering on LLM responses |
| **Authentication** | Add auth layer (OAuth2/JWT) for production |
| **Rate limiting** | Implement per-user rate limits |
| **Data residency** | Self-host models and data for compliance |
| **PII handling** | Wikipedia data is public; no PII concerns for this use case |
| **Audit logging** | Log all queries for compliance and debugging |

## 7. Scalability Concerns

### Horizontal Scaling
- **Web tier:** Stateless Streamlit/FastAPI behind load balancer
- **Model serving:** GPU pool with auto-scaling
- **Vector DB:** Managed service with auto-scaling (Pinecone/Qdrant Cloud)
- **Cache:** Redis cluster for frequent queries

### Bottlenecks and Solutions
| Bottleneck | Solution |
|-----------|----------|
| LLM inference speed | GPU batching, model quantization, caching |
| Embedding generation | Pre-compute; batch at ingestion time |
| Vector search at scale | Managed vector DB with indexing (HNSW/IVF) |
| Concurrent users | Stateless API + horizontal scaling |
| Data freshness | Scheduled incremental re-ingestion |

### Cost Optimization
- Use quantized models (GGUF/AWQ) to reduce GPU memory
- Cache frequent queries and their embeddings
- Implement tiered storage for less-accessed entities
- Consider serverless GPU (Modal, RunPod) for burst traffic

## 8. Tradeoffs and Limitations

### Current Design Tradeoffs
| Decision | Tradeoff |
|----------|----------|
| Single vector store | Simpler but requires metadata filtering overhead |
| Rule-based classification | Fast but less accurate than ML-based |
| Fixed chunk size | Simple but may split semantic units |
| Small model (3B) | Fast on CPU but lower quality than 7B+ |
| No conversation memory | Stateless but can't handle follow-ups |

### Production Tradeoffs
| Decision | Tradeoff |
|----------|----------|
| Managed vector DB | Higher cost but lower operational burden |
| Larger model (7B+) | Better quality but needs GPU |
| Real-time ingestion | Fresher data but more complex pipeline |
| Hybrid search (BM25 + vector) | Better recall but more infrastructure |

### When NOT to Use This Architecture
- **Real-time data needs** — RAG adds latency; consider fine-tuning
- **Very large corpora (>1M docs)** — Consider specialized search engines
- **Multi-modal queries** — Requires different embedding models
- **Mission-critical accuracy** — RAG + small models have inherent limitations
