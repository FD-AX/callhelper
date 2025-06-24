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

embedding = HuggingFaceEmbeddings()

vectorstore = Qdrant(
    client=qdrant_client,
    collection_name="messages",
    embeddings=embedding
)

async def save_message_to_qdrant(message: str, communication_id: str):
    now = datetime.datetime.now(datetime.timezone.utc)
    doc = Document(
        page_content=message,
        metadata={
            "communication_id": communication_id,
            "timestamp": now.isoformat()
        }
    )
    vectorstore.add_documents([doc])