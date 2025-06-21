import streamlit as st
import logging
from dotenv import load_dotenv
from ai_code.utils import load_yaml_config
from ai_code.prompt_builder import build_prompt_from_config
from langchain_groq import ChatGroq
from ai_code.paths import APP_CONFIG_FPATH, PROMPT_CONFIG_FPATH
from ai_code.vector_db_ingest import get_db_collection, embed_documents

# Load environment
load_dotenv()
collection = get_db_collection(collection_name="publications")

# Setup logging
logging.basicConfig(level=logging.INFO)

# Load configs
app_config = load_yaml_config(APP_CONFIG_FPATH)
prompt_config = load_yaml_config(PROMPT_CONFIG_FPATH)
rag_prompt_template = prompt_config["rag_assistant_prompt"]

# Set defaults
llm_model = app_config["llm"]
default_k = app_config["vectordb"]["n_results"]
default_threshold = app_config["vectordb"]["threshold"]

# Page setup
st.set_page_config(page_title="RAG Assistant", layout="centered")
st.title("📚 Reserve Bank RAG Assistant")
st.markdown("Hi, you can ask a question about e-payments, and I will assist you 😊.")

# Sidebar - configuration
st.sidebar.header("🔧 Retrieval Settings")
n_results = st.sidebar.slider("Top K Results", 1, 20, default_k)
threshold = st.sidebar.slider("Distance Threshold", 0.0, 2.0, default_threshold, 0.05)
llm_choice = st.sidebar.text_input("LLM Model", value=llm_model)

# User query input
query = st.text_area("Enter your query:", height=150)
submit = st.button("🔍 Ask")


# Core functions
def retrieve_relevant_documents(query: str,
                                n_results: int, 
                                threshold: float) -> list[str]:
    """Retrieve relevant documents from the database based on the query."""
    st.info("Embedding query and retrieving documents...")
    query_embedding = embed_documents([query])[0]
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results,
        include=["documents", "distances"],
    )

    relevant_documents = []
    for doc, dist in zip(results["documents"][0], results["distances"][0]):
        if dist < threshold:
            relevant_documents.append(doc)
    return relevant_documents


def respond_to_query(query: str, 
                     n_results: int,
                     threshold: float, model: str) -> str:
    """ Respond to user query based on retrieved documents"""
    
    relevant_docs = retrieve_relevant_documents(query, n_results, threshold)
    if not relevant_docs:
        return "No relevant documents found."

    st.markdown("### 📄 Relevant Documents")
    for i, doc in enumerate(relevant_docs, 1):
        st.markdown(f"**Doc {i}:** {doc[:500]}...")  # Show snippet

    input_data = f"Relevant documents:\n\n{relevant_docs}\n\nUser's question:\n\n{query}"
    prompt = build_prompt_from_config(rag_prompt_template, input_data=input_data)

    st.info("Sending prompt to LLM...")
    llm = ChatGroq(model=model)
    response = llm.invoke(prompt)

    return response.content


# Response
if submit and query:
    with st.spinner("Generating response..."):
        answer = respond_to_query(query, n_results, threshold, llm_choice)
        st.markdown("### 💬 Assistant's Answer")
        st.success(answer)
