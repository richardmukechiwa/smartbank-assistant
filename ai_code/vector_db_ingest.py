import os
print("Current working directory:", os.getcwd())

import os
import torch
import chromadb
import shutil
from paths import VECTOR_DB_DIR
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter

def initialize_db(
    persist_directory: str = VECTOR_DB_DIR,
    collection_name: str = "publications",
    delete_existing: bool = False,
) -> chromadb.Collection:
    """
    Initialize a new vector database collection.

    Args:
        persist_directory (str, optional): _description_. 
            Defaults to VECTOR_DB_DIR.
        collection_name (str, optional): _description_. 
        Defaults to "publications".
        delete_existing (bool, optional): _description_. Defaults to False.

    Returns:
        chromadb.Collection: _description_
    """
    if os.path.exists(persist_directory) and delete_existing:
        shutil.rmtree(persist_directory)
        
    os.makedirs(persist_directory, exist_ok=True)
    
    # initialize ChromaDB client with persistent storage
    client = chromadb.PersistentClient(path=persist_directory)
    
    # Create or get a collection
    try:
        # Try to get existing collection first
        collection=client.get_collection(name=collection_name) 
        print(f"Retrieval existing collection: {collection_name}")
    except Exception:
        # If collection doesn't exist, create it
        collection = client.create_collection(
            name=collection_name,         
            metadata={
                "hnsw:space": "cosine",
                "hnsw:batch_size": 1000
            }, # Use cosine distance for semantic search
        )    
        print(f"Created new collection: {collection_name}")
        
    print(f"ChromaDB initialized with persistent storage at: {persist_directory}")
    
    return collection


def chunk_publications(
    publication: str, chunk_size: int = 1000, chunk_overlap: int = 200
) -> list[str]:
    """ Chunk a list of publications into smaller lists.
    """
    loader = PyPDFLoader(publication)
    publication = loader.load()
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )
    return text_splitter.split_text(publication)
def embed_documents(documents: list[str]) -> list[list[float]]:
    """
    Embed documents using a model
    """
    device = (
        "cuda" 
        if torch.cuda.is_available()
        else "mps" if torch.backends.mps.is_available() 
        else "cpu"
        
    )
    
    model = HuggingFaceEmbeddings(
        
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        model_kwargs={"device": device},
        
    )
    embeddings = model.embed_documents{documents}
    return embeddings 
        
        
        
        
    )
    

    
    

        
            
            
            
def main():
    collection = initialize_db(
        persist_directory=VECTOR_DB_DIR,
        collection_name="publications",
        delete_existing=True
    )   
    
    # publications = load_all_publications()
    # insert_publications{collection, publications}
    
    # print(f"Total documents in collection: {collection.count()}")  

    
if __name__ == "__main__":
    main()
    
    
    
    
    
