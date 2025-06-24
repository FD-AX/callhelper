from langchain_community.vectorstores import Qdrant
from qdrant_client import QdrantClient
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.schema import Document
import datetime
import os
from dotenv import load_dotenv

load_dotenv()

qdrant_client = QdrantClient(
    url=os.getenv("QDRANT_HOST"),
    api_key=os.getenv("QDRANT_API_KEY")
)

embedding = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

vectorstore = Qdrant(
    client=qdrant_client,
    collection_name="messages",
    embeddings=embedding
)

def save_message_to_qdrant(message: str, communication_id: str):
    now = datetime.datetime.now(datetime.timezone.utc)
    embedding_vector = embedding.embed_query(message)

    doc = Document(
        page_content=message,
        metadata={
            "communication_id": communication_id,
            "timestamp": now.isoformat(),
            "embedding": embedding_vector  # можно сохранить в метаданные, но Qdrant сам это не использует
        }
    )
    vectorstore.add_documents([doc])