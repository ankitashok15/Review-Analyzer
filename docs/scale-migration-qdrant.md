# Scale Migration Guide: pgvector → Qdrant

## When to migrate

- `review_embeddings` > 500K rows and search p95 > 1s
- Need multi-region replication or dedicated vector SLAs
- pgvector CPU/memory on Postgres becomes bottleneck

## Current architecture

- PostgreSQL 16 + pgvector extension
- HNSW index on `review_embeddings.embedding`
- 768-dim vectors (`gemini-embedding-001` with `output_dimensionality=768`)

## Target architecture

```
API / Workers → Qdrant (vectors) + PostgreSQL (metadata)
```

Keep `reviews` and `review_enrichments` in Postgres. Move vectors to Qdrant collection `reviews_v1`.

## Migration steps

### 1. Provision Qdrant

```yaml
# docker-compose addition
qdrant:
  image: qdrant/qdrant:latest
  ports:
    - "6333:6333"
  volumes:
    - qdrant_data:/qdrant/storage
```

### 2. Export vectors from Postgres

```sql
COPY (
  SELECT review_id::text, chunk_index, model_version, content_hash,
         embedding::text
  FROM review_embeddings
) TO '/tmp/embeddings.csv' CSV HEADER;
```

Or batch via `EmbeddingRepository` Python export script.

### 3. Create Qdrant collection

```python
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

client = QdrantClient(url="http://localhost:6333")
client.create_collection(
    collection_name="reviews_v1",
    vectors_config=VectorParams(size=768, distance=Distance.COSINE),
)
```

### 4. Upsert with payload filters

Payload fields: `source`, `platform`, `sentiment`, `review_date`, `model_version`.

### 5. Switch `VectorStore.similarity_search`

Replace SQL pgvector query with `QdrantClient.search()` in `src/storage/vector_store.py`.

### 6. Dual-write period

- Write new embeddings to both Postgres and Qdrant for 1 week
- Compare search results (top-10 overlap ≥95%)

### 7. Cutover

- Point semantic search to Qdrant only
- Keep Postgres embeddings as backup; drop after validation

## Rollback

Re-enable `EmbeddingRepository.find_similar` against pgvector if Qdrant fails.

## Effort estimate

1–2 days for export + dual-write; 1 day validation.
