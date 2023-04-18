from typing import Any
import openai
from qdrant_client import QdrantClient


class NeuralSearcher:
    def __init__(
        self,
        collection_name: str,
        openai_api_key: str,
        host: str | None,
        port: int | None = 6333,
        embedding_model: str = "text-embedding-ada-002",
        chat_model: str = "gpt-3.5-turbo-0301",
        is_cloud_qdrant: bool = False,
        url: str | None = None,
        api_key: str | None = None,
        **kwargs: Any,
    ):
        self.collection_name = collection_name
        # Initialize encoder model
        self.embedding_model = embedding_model
        self.chat_model = chat_model
        # initialize Qdrant client
        self.qdrant_client: QdrantClient = (
            QdrantClient(url=url, api_key=api_key, **kwargs)
            if is_cloud_qdrant
            else QdrantClient(host=host, port=port, **kwargs)
        )
        self.openai = openai
        self.openai.api_key = openai_api_key

    def get_embedding(self, text):
        text = text.replace("\n", " ")
        return self.openai.Embedding.create(input=[text], model=self.embedding_model)[
            "data"
        ][0]["embedding"]

    def search(self, text: str) -> list[dict[str, str]]:
        # Convert text query into vector
        vector = self.get_embedding(text=text)

        # Use `vector` for search for closest vectors in the collection
        search_result = self.qdrant_client.search(
            collection_name=self.collection_name,
            query_vector=vector,
            query_filter=None,  # We don't want any filters for now
            top=5,  # 5 the most closest results is enough
        )
        # `search_result` contains found vector ids with similarity scores along with the stored payload
        # In this function we are interested in payload only
        payloads = [hit.payload for hit in search_result]
        return payloads
