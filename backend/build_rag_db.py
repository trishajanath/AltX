import os
import shutil
from typing import List
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_community.vectorstores import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document

# Fix deprecation warning - use updated import
try:
    from langchain_huggingface import HuggingFaceEmbeddings
except ImportError:
    from langchain_community.embeddings import HuggingFaceEmbeddings

def load_documents_by_type(knowledge_base_path: str) -> List[Document]:
    """Load documents of different types from the knowledge base"""
    all_documents = []
    
    # Load .txt files
    try:
        txt_loader = DirectoryLoader(
            knowledge_base_path,
            glob="**/*.txt",
            loader_cls=TextLoader,
            loader_kwargs={'encoding': 'utf-8'}
        )
        txt_docs = txt_loader.load()
        all_documents.extend(txt_docs)
        print(f"📄 Loaded {len(txt_docs)} text files")
    except Exception as e:
        print(f"⚠️  Error loading text files: {e}")
    
    # Try to load .pdf files (if pypdf is available)
    try:
        from langchain_community.document_loaders import PyPDFLoader
        import glob
        
        pdf_files = glob.glob(os.path.join(knowledge_base_path, "**/*.pdf"), recursive=True)
        for pdf_file in pdf_files:
            try:
                pdf_loader = PyPDFLoader(pdf_file)
                pdf_docs = pdf_loader.load()
                all_documents.extend(pdf_docs)
                print(f"📄 Loaded PDF: {os.path.basename(pdf_file)}")
            except Exception as e:
                print(f"⚠️  Error loading {pdf_file}: {e}")
                
    except ImportError:
        print("📝 PyPDF not available, skipping PDF files")
    
    return all_documents

def build_database():
    print("🚀 Starting RAG database build...")
    
    # Configuration
    knowledge_base_path = "knowledge_base"
    vector_db_path = "vector_db"
    
    # Remove existing database
    if os.path.exists(vector_db_path):
        shutil.rmtree(vector_db_path)
        print("🗑️  Removed existing vector database")
    
    # Check if knowledge base exists
    if not os.path.exists(knowledge_base_path):
        print(f"❌ Knowledge base directory '{knowledge_base_path}' not found!")
        return
    
    try:
        # Load documents
        print(f"📂 Loading documents from {knowledge_base_path}...")
        documents = load_documents_by_type(knowledge_base_path)
        
        print(f"📄 Total loaded: {len(documents)} documents")
        
        if not documents:
            print("⚠️  No documents found in knowledge base!")
            return
        
        # Split documents into chunks
        print("✂️  Splitting documents into chunks...")
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
        
        splits = text_splitter.split_documents(documents)
        print(f"📝 Created {len(splits)} text chunks")
        
        # Create embeddings - Fixed deprecation
        print("🧠 Creating embeddings...")
        embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs={'device': 'cpu'}
        )
        
        # Create vector store
        print("💾 Building vector database...")
        vectorstore = Chroma.from_documents(
            documents=splits,
            embedding=embeddings,
            persist_directory=vector_db_path
        )
        
        # Persist the database
        vectorstore.persist()
        print("✅ Vector database saved successfully!")
        
        # Test the database
        print("🔍 Testing database...")
        test_queries = [
            "SQL injection prevention",
            "password security",
            "secure coding practices",
            "eval() code injection",
            "XSS prevention"
        ]
        
        for query in test_queries:
            results = vectorstore.similarity_search(query, k=1)
            print(f"📊 Query: '{query}' -> {len(results)} results")
            if results:
                print(f"    Preview: {results[0].page_content[:100]}...")
        
        print("🎉 RAG database build completed successfully!")
        
    except Exception as e:
        print(f"❌ Error building database: {str(e)}")
        raise

if __name__ == "__main__":
    build_database()