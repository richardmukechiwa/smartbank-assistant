import streamlit as st
import logging
import os
from dotenv import load_dotenv
from ai_code.utils import load_yaml_config
from ai_code.prompt_builder import build_prompt_from_config
from langchain_groq import ChatGroq
from ai_code.paths import APP_CONFIG_FPATH, PROMPT_CONFIG_FPATH
from ai_code.vector_db_ingest import get_db_collection, embed_documents
from PIL import Image

# Load environment
load_dotenv()
collection = get_db_collection(collection_name="publications")

# Logging
logging.basicConfig(level=logging.INFO)

# Load configs
app_config = load_yaml_config(APP_CONFIG_FPATH)
prompt_config = load_yaml_config(PROMPT_CONFIG_FPATH)
rag_prompt_template = prompt_config["rag_assistant_prompt"]

# Defaults
llm_model = app_config["llm"]
default_k = app_config["vectordb"]["n_results"]
default_threshold = app_config["vectordb"]["threshold"]

# Page config
st.set_page_config(
    page_title="RAG Assistant - Reserve Bank",
    page_icon="assets/RESERVE_BANK_OF_ZIMBABWE_LOGO.png",
    layout="centered"
)

# Header with logo and title
col1, col2 = st.columns([1, 5])
with col1:
    st.image("assets/RESERVE_BANK_OF_ZIMBABWE_LOGO.png", width=80)
with col2:
    st.markdown("<h1 style='margin-top: 15px;'>Reserve Bank RAG Assistant</h1>", unsafe_allow_html=True)

st.markdown("<p style='text-align: center;'>Ask anything about e-payments, and I’ll help you find the answer 💬</p>", unsafe_allow_html=True)
st.markdown("---")

# Sidebar
with st.sidebar:
    st.header("🔧 Retrieval Settings")
    n_results = st.slider("Top K Results", 1, 20, default_k)
    threshold = st.slider("Distance Threshold", 0.0, 2.0, default_threshold, step=0.05)
    llm_choice = st.text_input("LLM Model", value=llm_model)
    st.markdown("---")
    st.caption("Powered by LangChain + Groq")

# Example queries
with st.expander("💡 Example Queries", expanded=False):
    st.markdown("""
    - What are important POS safety tips for retailers?,
    - How can retailers detect POS tampering?,
    - Why is it important to secure the position of POS terminals?
    """)

# Input
query = st.text_area("📥 Enter your query:", placeholder="E.g., What are the limits on mobile e-transfers?", height=150)
submit = st.button("🔍 Ask Assistant")

# Core logic
def retrieve_relevant_documents(query: str, n_results: int, threshold: float) -> list[str]:
    """Retrieve documents from ChromaDB based on the query."""
    st.info("🔎 Embedding query and retrieving documents...")
    query_embedding = embed_documents([query])[0]
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results,
        include=["documents", "distances"],
    )
    relevant_documents = [
        doc for doc, dist in zip(results["documents"][0], results["distances"][0]) if dist < threshold
    ]
    return relevant_documents


def respond_to_query(query: str, n_results: int, threshold: float, model: str) -> str:
    """ Respond to a query by retrieving relevant documents and generating a response."""
    relevant_docs = retrieve_relevant_documents(query, n_results, threshold)
    if not relevant_docs:
        return "No relevant documents found."

    with st.expander("📄 Show Relevant Documents"):
        for i, doc in enumerate(relevant_docs, 1):
            st.markdown(f"**Doc {i}:** {doc[:400]}...")

    input_data = f"Relevant documents:\n\n{relevant_docs}\n\nUser's question:\n\n{query}"
    prompt = build_prompt_from_config(rag_prompt_template, input_data=input_data)

    st.info("🤖 Sending prompt to the LLM...")
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        st.error("❌ GROQ_API_KEY is not set. Please check your .env file.")
        return ""

    llm = ChatGroq(model=model, api_key=api_key)
    response = llm.invoke(prompt)
    return response.content


# Output
if submit and query:
    with st.spinner("💡 Generating response..."):
        answer = respond_to_query(query, n_results, threshold, llm_choice)
        if answer:
            with st.chat_message("assistant"):
                st.markdown("### 💬 Assistant’s Answer")
                st.write(answer)

# Footer
st.markdown("---")
st.caption("Made with ❤️ by Richard Mukechiwa | [GitHub](https://github.com/richardmukechiwa/smartbank-assistant)")
