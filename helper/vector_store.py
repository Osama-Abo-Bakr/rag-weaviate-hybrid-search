import weaviate
import logging
from typing import List
from dotenv import load_dotenv
from langchain_huggingface.embeddings import HuggingFaceEmbeddings
from langchain_weaviate import WeaviateVectorStore

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


# Load environment variables
load_dotenv()

def create_vector_db(vector_store_id: str):
    """
    Creates a vector database in Weaviate.

    Args:
        vector_store_id (str): The name of the vector database to create.

    Returns:
        None
    """
    logger.info("🚀 Creating Vector DB...")
    weaviate_client = weaviate.connect_to_local()
    _ = weaviate_client.collections.create(vector_store_id)
    logger.info("✅ Vector DB Created Successfully! 🚀")
    weaviate_client.close()
    logger.info("🔌 Weaviate Connection Closed....")
    return
    

def adding_vector_db(vector_store_id: str, documents: List[str]) -> WeaviateVectorStore:
    """
    Create or Adds a vector database to Weaviate.

    Args:
        vector_store_id (str): The name of the vector database to add.
        documents (List[str]): The list of documents to add to the vector database.

    Returns:
        WeaviateVectorStore: The created vector database.

    Raises:
        Exception: If the vector database creation fails.
    """
    embeddings_model = HuggingFaceEmbeddings(
        model_name="./models/intfloat_multilingual_e5_large",
        model_kwargs={'device': 'cpu'},
        encode_kwargs={'normalize_embeddings': False}
    )
    
    logger.info("✈️ Connecting to Weaviate...")
    try:
        weaviate_client = weaviate.connect_to_local()
        if not weaviate_client.collections.exists(vector_store_id):
            logger.info("💫 Creating Vector DB...")
            _ = WeaviateVectorStore.from_texts(texts=documents, embedding=embeddings_model,
                                            client=weaviate_client, index_name=vector_store_id)
            
            logger.info("✅ Vector DB Created Successfully! 🚀")
        
        else:
            logger.info("😊 Added to Vector DB...")
            
            # ✅ Adding Documents to Vector DB
            _ = WeaviateVectorStore(
                client=weaviate_client, index_name=vector_store_id, 
                text_key="text", embedding=embeddings_model
            ).add_texts(texts=documents)
            
            logger.info("✅ Documents are Added to Vector DB Successfully! 🚀")
    
    except Exception as e:
        logger.error(f"Vector DB Creation Failed: {e}")
        raise
    
    finally:
        weaviate_client.close()
        logger.info("🔌 Weaviate Connection Closed.")
    

def delete_vector_db(vector_store_id: str) -> None:
    """
    Deletes a vector database from Weaviate.

    Args:
        vector_store_id (str): The name of the vector database to delete.

    Returns:
        None
    """
    logger.info("✈️ Connecting to Weaviate...")
    try:
        weaviate_client = weaviate.connect_to_local()
        weaviate_client.collections.delete(vector_store_id)
        logger.info("✅ Vector DB Deleted Successfully! 🚀")
        
    except Exception as e:
        logger.error(f"Vector DB Deletion Failed: {e}")
        raise
    finally:
        weaviate_client.close()
        logger.info("🔌 Weaviate Connection Closed.")
    
def loading_vector_db(vector_store_id: str) -> WeaviateVectorStore:
    """
    Loads a vector database from Weaviate.

    Args:
        vector_store_id (str): The name of the vector database to load.

    Returns:
        WeaviateVectorStore: The loaded vector database.

    Raises:
        Exception: If the vector database loading fails.
    """
    try:
        logger.info("✈️ Connecting to Weaviate...")
        # Ensure embeddings are correctly set
        embeddings_model = HuggingFaceEmbeddings(
            model_name="./models/intfloat_multilingual_e5_large",
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': False}
        )
        
        weaviate_client = weaviate.connect_to_local()
        vector_db = WeaviateVectorStore(client=weaviate_client, index_name=vector_store_id, 
                                        text_key='text', embedding=embeddings_model)
        logger.info("✈️ Weaviate Connection Established! 🚀")
        
        # ✅ Return both the vector store and client
        return vector_db, weaviate_client
    except Exception as e:
        logger.error(f"Vector DB Loading Failed: {e}")
        raise
    

def get_num_of_docs(vector_store_id: str) -> int:
    logger.info("✈️ Connecting to Weaviate...")
    client = weaviate.connect_to_local()
    
    collection = client.collections.get(vector_store_id)
    num_obj = len(collection.query.fetch_objects(limit=5000).objects)
    
    client.close()
    logger.info("🔌 Weaviate Connection Closed.")
    return num_obj