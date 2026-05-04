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
    Re-rank retrieved chunks by boosting those whose entity name
    appears in the query. This simple heuristic significantly improves
    retrieval relevance when the user mentions a specific entity.

    Chunks mentioning the queried entity get their distance reduced (boosted).
    """
    query_lower = query.lower()
    reranked = []

    for chunk in chunks:
        entity_name = chunk["metadata"]["entity_name"].lower()
        distance = chunk["distance"]

        # Check if entity name (or parts of it) appear in query
        name_parts = entity_name.split()
        query_words = set(query_lower.split())
        # Skip common short words that cause false matches
        skip_words = {"the", "of", "da", "jr", "jr.", "and", "in", "at", "to"}
        # Match if any significant part of the name is in the query words
        name_match = any(
            part in query_words
            for part in name_parts
            if len(part) > 3 and part not in skip_words
        )

        if name_match:
            # Boost matching entities by reducing their distance
            chunk["distance"] = distance * 0.5
            chunk["_boosted"] = True

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
    # even when semantic search ranks them lower
    fetch_count = max(n_results * 5, 50)

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
