"""
Generation module.
Uses a local Ollama LLM to generate answers grounded in retrieved context.
No external API calls — everything runs on localhost.
"""

import ollama

# Default model — can be changed to phi3 or mistral
LLM_MODEL = "llama3.2:3b"

SYSTEM_PROMPT = """You are a local Wikipedia RAG assistant. Your job is to answer questions using ONLY the provided context from Wikipedia articles.

Rules:
1. Answer the question using ONLY the information in the provided context.
2. If the answer is not present in the context, respond with: "I don't know based on the available data."
3. Do NOT make up information or use knowledge outside the provided context.
4. Be concise but informative in your answers.
5. When comparing entities, use information from the context about each entity.
6. If asked about something not in the context at all, say you don't know."""


def build_prompt(query: str, chunks: list[dict]) -> str:
    """
    Build the prompt for the LLM with the query and retrieved context.
    """
    context_parts = []
    for i, chunk in enumerate(chunks, 1):
        entity = chunk["metadata"]["entity_name"]
        source = chunk["metadata"]["source_url"]
        context_parts.append(
            f"[Source {i}: {entity}]\n{chunk['text']}\n(Source: {source})"
        )

    context_text = "\n\n---\n\n".join(context_parts)

    prompt = f"""Context from Wikipedia:
{context_text}

Question: {query}

Answer based only on the context above:"""

    return prompt


def generate_answer(query: str, chunks: list[dict], model: str = None) -> str:
    """
    Generate an answer using the local LLM and retrieved context.

    Args:
        query: The user's question
        chunks: List of retrieved chunk dicts with text and metadata
        model: Override for the LLM model name

    Returns:
        The generated answer string
    """
    if not chunks:
        return "I don't know based on the available data. No relevant context was found for your question."

    model = model or LLM_MODEL
    prompt = build_prompt(query, chunks)

    try:
        response = ollama.chat(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            options={
                "temperature": 0.3,  # Lower temperature for more factual answers
                "num_predict": 512,  # Limit response length
            },
        )
        return response["message"]["content"]
    except Exception as e:
        return (
            f"Error generating answer. Is Ollama running with '{model}' pulled?\n"
            f"Run: ollama pull {model}\n"
            f"Error: {e}"
        )


def generate_answer_stream(query: str, chunks: list[dict], model: str = None):
    """
    Generate an answer using streaming for real-time display.
    Yields chunks of the response as they are generated.
    """
    if not chunks:
        yield "I don't know based on the available data. No relevant context was found for your question."
        return

    model = model or LLM_MODEL
    prompt = build_prompt(query, chunks)

    try:
        stream = ollama.chat(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            options={
                "temperature": 0.3,
                "num_predict": 512,
            },
            stream=True,
        )
        for chunk in stream:
            yield chunk["message"]["content"]
    except Exception as e:
        yield (
            f"Error generating answer. Is Ollama running with '{model}' pulled?\n"
            f"Run: ollama pull {model}\n"
            f"Error: {e}"
        )


def check_llm_model(model: str = None) -> bool:
    """Check if the LLM model is available in Ollama."""
    model = model or LLM_MODEL
    try:
        models = ollama.list()
        model_names = [m.model for m in models.models]
        return any(model in name for name in model_names)
    except Exception:
        return False
