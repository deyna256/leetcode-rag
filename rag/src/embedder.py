from openai import OpenAI

from .config import settings

_client: OpenAI | None = None
BATCH_SIZE = 100


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(api_key=settings.OPENAI_API_KEY)
    return _client


def embed_texts(texts: list[str]) -> list[list[float]]:
    client = _get_client()
    all_embeddings: list[list[float]] = []
    for i in range(0, len(texts), BATCH_SIZE):
        batch = texts[i : i + BATCH_SIZE]
        resp = client.embeddings.create(input=batch, model=settings.EMBEDDING_MODEL)
        all_embeddings.extend([d.embedding for d in resp.data])
    return all_embeddings
