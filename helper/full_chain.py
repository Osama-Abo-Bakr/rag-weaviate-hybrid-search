import os
import logging
from dotenv import load_dotenv
from typing import List, Optional
from langchain_core.prompts import PromptTemplate
from langchain_cohere import CohereRerank
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.retrievers import ContextualCompressionRetriever
from langchain.chains import ConversationalRetrievalChain
from helper.vector_store import loading_vector_db, get_num_of_docs
from helper.db_connection import get_chat_history, save_chat_history

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def create_retriever_chain(vector_store_id: str) -> Optional[ConversationalRetrievalChain]:
    # loading Vector-db & LLM
    vectorstore, weaviate_client = loading_vector_db(vector_store_id=vector_store_id)
    try:
        llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash-thinking-exp-01-21", 
                                    api_key=os.getenv("GOOGLE_API_KEY"))
        
        template = """
        You are an AI assistant specializing in document-based question answering.  
        Your task is to answer questions based on uploaded files, including books, PDFs, and PPTs, using a Retrieval-Augmented Generation (RAG) system.  

        Use the following extracted content from the document to provide an accurate response in markdown format (highly structured):  
        {context}  

        Question: {question}  

        If the provided context does not contain relevant information, explicitly state:  
        "The retrieved context does not provide relevant information." Then, generate the response based on your own knowledge.  

        Answer the question strictly based on the provided context if relevant. If the context is insufficient, state that more information is needed.  
        """

        prompt = PromptTemplate(
            input_variables=["context", "question"], 
            template=template
        )
        
        # Base Retriever
        logger.info("💫 Creating Base Retriever...")
        retriever = vectorstore.as_retriever(search_type="mmr", search_kwargs={"k": 5, "fetch_k": 10}, alpha=0.5)
        logger.info("✅ Base Retriever Created Successfully! 🚀")
        # Reranker.
        reranker = CohereRerank(
            cohere_api_key=os.getenv("COHERE_API_KEY"),  model="rerank-english-v3.0"
        )
        # Compression Retriever (Re-Ranker + Base Retriever)
        compression_retriever = ContextualCompressionRetriever(
            base_compressor=reranker, base_retriever=retriever
        )
        
        return ConversationalRetrievalChain.from_llm(
            llm=llm,
            retriever=compression_retriever, # Re-Ranker + Base Retriever
            return_source_documents=True,
            combine_docs_chain_kwargs={"prompt": prompt, "document_variable_name": "context"},
        ), weaviate_client
        
    except Exception as e:
        logger.error(f"🚫 Retriever Chain Creation Failed! {e}🚫")
        raise
    

def simple_chat(user_query: str) -> str:
    """
    A simple chat function that uses the ChatGoogleGenerativeAI model to generate a response to user_query.

    Args:
        user_query (str): The user's query to generate a response to.

    Returns:
        str: The generated response to the user's query.
    """
    llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash-thinking-exp-01-21")
    result = llm.invoke(user_query)
    return {"answer": result.content}
    

def get_response(question: str, vector_store_id: str, user_id: str, project_id: str) -> dict:  
    """
    Generates a response to a question using a retrieval-augmented generation system.

    This function first checks if there are documents in the specified vector store.
    If documents are present, it fetches the chat history and creates a retriever chain to generate a response.
    If no documents are found, it uses a simpler chat model to generate the response.

    The generated response is then saved to the chat history in the database.

    Args:
        question (str): The question to generate a response for.
        vector_store_id (str): The ID of the vector store to use.
        user_id (str): The ID of the user asking the question.
        project_id (str): The ID of the project context for the question.

    Returns:
        dict: A dictionary containing the generated response.
    """
    try:
        logger.info("💫 Fetching Chat History...")
        chat_history = get_chat_history(vector_id=vector_store_id)
        chat_history_list = [(entry["user_query"], entry["chatbot_answer"]) for entry in chat_history]
        logger.info("✅ Chat History Fetched Successfully! 🚀")
    except Exception as e:
        logger.error(f"🚫 Chat History Fetch Failed! {e}🚫")
        chat_history = []
        
    if get_num_of_docs(vector_store_id) > 0:           
        logger.info("💫 Creating Retriever Chain...")
        retriever_chain, weaviate_client = create_retriever_chain(vector_store_id=vector_store_id)
        response = retriever_chain.invoke({"question": question, "chat_history": chat_history_list})
        logger.info("✅ Retriever Chain Created Successfully! 🚀")
        
        weaviate_client.close()
        logger.info("🛑 Closing Weaviate Client...")
        
    else:
        response = simple_chat(user_query=question)
        
    logger.info("💫 Saving Chat History...")
    result = response["answer"].replace("```markdown", "").replace("```", "")
    new_entry = {"user_query": question, "chatbot_answer": result}
    chat_history.append(new_entry)
    save_chat_history(chat_history=chat_history, user_id=user_id, project_id=project_id, vector_id=vector_store_id)
    logger.info("✅ Chat History Saved Successfully! 🚀")
    
    return response