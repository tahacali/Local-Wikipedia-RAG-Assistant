"""
Retrieval module.
Handles query classification and context retrieval from the vector store.

Query Classification Strategy:
- Rule-based keyword matching (simple, transparent, effective)
- Checks for person-related and place-related keywords in the query
- If both types of keywords are found, classifies as "both"
- If neither is found, defaults to "both" for maximum recall
"""

from src.embeddings import get_embedding
from src.vector_store import get_collection


# Keywords that suggest a query is about people
PERSON_KEYWORDS = [
    "who", "person", "people", "he", "she", "born", "died", "life",
    "career", "discovered", "invented", "wrote", "composed", "painted",
    "played", "athlete", "scientist", "artist", "author", "musician",
    "singer", "actor", "leader", "president", "king", "queen",
    "footballer", "player", "goals", "albums", "songs", "nobel",
    # Entity names as keywords for better classification
    "einstein", "curie", "vinci", "shakespeare", "lovelace", "tesla",
    "messi", "ronaldo", "swift", "kahlo", "newton", "cleopatra",
    "gandhi", "luther king", "napoleon", "mozart", "aristotle",
    "darwin", "mandela", "earhart",
]

# Keywords that suggest a query is about places
PLACE_KEYWORDS = [
    "where", "place", "located", "location", "built", "tall", "high",
    "monument", "building", "tower", "wall", "temple", "canyon", "mountain",
    "statue", "pyramid", "falls", "reef", "ruins", "ancient",
    "landmark", "heritage", "site", "visit", "tourist",
    # Entity names as keywords
    "eiffel", "great wall", "taj mahal", "grand canyon", "machu picchu",
    "colosseum", "hagia sophia", "statue of liberty", "pyramids", "giza",
    "everest", "stonehenge", "petra", "angkor", "christ the redeemer",
    "barrier reef", "niagara", "chichen itza", "acropolis", "fuji",
    "victoria falls",
]


def classify_query(query: str) -> str:
    """
    Classify a user query as 'person', 'place', 'both', or 'unknown'.

    Uses simple keyword matching against predefined keyword lists.
    Falls back to 'both' when uncertain to maximize recall.
    """
    query_lower = query.lower()
    # Split into words for single-word keyword matching (avoids "he" matching "the")
    query_words = set(query_lower.split())

    def has_keyword_match(keywords):
        for kw in keywords:
            if " " in kw:
                # Multi-word keywords: use substring matching
                if kw in query_lower:
                    return True
            else:
                # Single-word keywords: match whole words only
                if kw in query_words:
                    return True
        return False

    has_person_keyword = has_keyword_match(PERSON_KEYWORDS)
    has_place_keyword = has_keyword_match(PLACE_KEYWORDS)

    if has_person_keyword and has_place_keyword:
        return "both"
    elif has_person_keyword:
        return "person"
    elif has_place_keyword:
        return "place"
    else:
        # Default to 'both' for maximum recall on ambiguous queries
        return "both"


def _rerank_chunks(chunks: list[dict], query: str) -> list[dict]:
    """
    Re-rank retrieved chunks using two heuristics:
    1. Entity-name boosting: chunks whose entity name appears in the query
       get a strong distance reduction.
    2. Keyword-content boosting: chunks whose text contains important query
       keywords get a moderate distance reduction. This helps surface chunks
       that are keyword-relevant but semantically distant (e.g., searching
       for "Turkey" should surface Hagia Sophia chunks that mention Turkey).

    Chunks mentioning the queried entity get their distance reduced (boosted).
    """
    query_lower = query.lower()
    # Strip punctuation from query words
    query_words = set(
        w.strip("?.,!;:'\"()[]{}") for w in query_lower.split()
    )

    # Common stopwords to ignore for keyword matching
    stopwords = {
        "the", "of", "da", "jr", "jr.", "and", "in", "at", "to", "a", "an",
        "is", "was", "are", "were", "it", "its", "this", "that", "which",
        "who", "what", "where", "when", "why", "how", "for", "with", "from",
        "about", "tell", "me", "can", "you", "do", "does", "did", "has",
        "have", "had", "be", "been", "being", "will", "would", "could",
        "should", "may", "might", "shall", "not", "no", "or", "but", "if",
        "than", "so", "very", "just", "also", "most", "some", "any", "all",
        "many", "much", "more", "other", "between", "famous", "known",
        "located", "compare", "important",
        # Domain-specific generic words that appear in most chunks
        "place", "person", "people", "city", "country", "world", "history",
        "used", "built", "made", "called", "named", "one", "two", "first",
    }

    # Extract significant keywords from the query (non-stopwords, length > 2)
    significant_keywords = {
        w for w in query_words
        if w not in stopwords and len(w) > 2
    }

    reranked = []

    for chunk in chunks:
        entity_name = chunk["metadata"]["entity_name"].lower()
        distance = chunk["distance"]
        boost_applied = False

        # --- Heuristic 1: Entity-name boosting ---
        name_parts = entity_name.split()
        skip_words = {"the", "of", "da", "jr", "jr.", "and", "in", "at", "to"}
        name_match = any(
            part in query_words
            for part in name_parts
            if len(part) > 3 and part not in skip_words
        )

        if name_match:
            chunk["distance"] = distance * 0.5
            chunk["_boosted"] = True
            boost_applied = True

        # --- Heuristic 2: Keyword-content boosting ---
        # Check if significant query keywords appear in the chunk text
        if significant_keywords and not boost_applied:
            chunk_text_lower = chunk["text"].lower()
            matched_keywords = sum(
                1 for kw in significant_keywords
                if kw in chunk_text_lower
            )
            if matched_keywords > 0:
                # Moderate boost proportional to keyword matches
                keyword_boost = 0.85 ** matched_keywords
                chunk["distance"] = chunk["distance"] * keyword_boost
                chunk["_keyword_boosted"] = True

        reranked.append(chunk)

    # Sort by (possibly boosted) distance
    reranked.sort(key=lambda c: c["distance"])
    return reranked


def retrieve_context(query: str, n_results: int = 8, query_type: str = None) -> dict:
    """
    Retrieve relevant chunks from the vector store based on the query.

    Uses semantic search with optional metadata filtering, then re-ranks
    results to boost chunks whose entity name appears in the query.

    Args:
        query: The user's question
        n_results: Number of chunks to return (fetches more internally for re-ranking)
        query_type: Override for query classification (person/place/both/None)

    Returns:
        Dictionary with:
        - query_type: The classified query type
        - chunks: List of retrieved chunk dicts with text and metadata
    """
    # Classify the query if not provided
    if query_type is None:
        query_type = classify_query(query)

    # Generate query embedding (uses "search_query" prefix by default)
    query_embedding = get_embedding(query, prefix="search_query")

    # Build filter based on query type
    where_filter = None
    if query_type == "person":
        where_filter = {"entity_type": "person"}
    elif query_type == "place":
        where_filter = {"entity_type": "place"}
    # For 'both' or 'unknown', no filter - search everything

    # Fetch more results than needed for re-ranking pool
    # A large pool ensures the re-ranker can boost entity-name matches
    # and keyword-content matches even when semantic search ranks them lower
    fetch_count = max(n_results * 5, 150)

    # Query ChromaDB
    collection = get_collection()

    try:
        query_params = {
            "query_embeddings": [query_embedding],
            "n_results": fetch_count,
            "include": ["documents", "metadatas", "distances"],
        }
        if where_filter:
            query_params["where"] = where_filter

        results = collection.query(**query_params)
    except Exception as e:
        return {
            "query_type": query_type,
            "chunks": [],
            "error": f"Retrieval failed: {e}",
        }

    # Format results
    chunks = []
    if results and results["documents"] and results["documents"][0]:
        for i, doc in enumerate(results["documents"][0]):
            chunks.append({
                "text": doc,
                "metadata": results["metadatas"][0][i],
                "distance": results["distances"][0][i],
            })

    # Re-rank: boost chunks whose entity name appears in the query
    chunks = _rerank_chunks(chunks, query)

    # Return top n_results after re-ranking
    return {
        "query_type": query_type,
        "chunks": chunks[:n_results],
    }
