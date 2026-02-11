import os
from langchain.chains import RetrievalQA
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.chat_models import ChatOllama
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.vectorstores import FAISS

VECTOR_DIR = os.path.join(os.path.dirname(__file__), "vectorstore")
VECTOR_INDEX = os.path.join(VECTOR_DIR, "index.faiss")

EMBED_MODEL = os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text")
CHAT_MODEL = os.getenv("OLLAMA_CHAT_MODEL", "llama3.1")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
embeddings = OllamaEmbeddings(model=EMBED_MODEL, base_url=OLLAMA_BASE_URL)
llm = ChatOllama(model=CHAT_MODEL, temperature=0, base_url=OLLAMA_BASE_URL)

_vectorstore = None


def _load_vectorstore():
    global _vectorstore
    if _vectorstore is not None:
        return _vectorstore

    if os.path.exists(VECTOR_INDEX):
        _vectorstore = FAISS.load_local(
            VECTOR_DIR,
            embeddings,
            allow_dangerous_deserialization=True,
        )

    return _vectorstore


def get_status():
    return _load_vectorstore() is not None


def ingest_pdf(file_path):
    loader = PyPDFLoader(file_path)
    documents = loader.load()
    chunks = text_splitter.split_documents(documents)

    vectorstore = _load_vectorstore()
    if vectorstore is None:
        vectorstore = FAISS.from_documents(chunks, embeddings)
    else:
        vectorstore.add_documents(chunks)

    vectorstore.save_local(VECTOR_DIR)
    global _vectorstore
    _vectorstore = vectorstore

    return {
        "status": "ingested",
        "chunks": len(chunks),
        "file": os.path.basename(file_path),
    }


def ask_rag(query):
    vectorstore = _load_vectorstore()
    if vectorstore is None:
        raise ValueError("Vector store is empty. Ingest a PDF first.")

    retriever = vectorstore.as_retriever(search_kwargs={"k": 4})
    qa = RetrievalQA.from_chain_type(
        llm=llm,
        retriever=retriever,
        chain_type="stuff",
    )
    result = qa.invoke({"query": query})
    return result.get("result", "")
