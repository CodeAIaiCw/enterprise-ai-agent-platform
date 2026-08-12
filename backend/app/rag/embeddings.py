from fastembed import TextEmbedding


MODEL_NAME = "BAAI/bge-small-en-v1.5"


class EmbeddingService:
    def __init__(self) -> None:
        self.model = TextEmbedding(
            model_name=MODEL_NAME
        )

    def embed_text(
        self,
        text: str,
    ) -> list[float]:
        cleaned_text = text.strip()

        if not cleaned_text:
            raise ValueError(
                "Cannot embed empty text"
            )

        embeddings = self.model.embed(
            [cleaned_text]
        )

        vector = next(embeddings)

        return vector.tolist()


embedding_service = EmbeddingService()