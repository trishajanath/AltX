import os
import shutil
from typing import List
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document

# Fix deprecation warning - use updated import
try:
    from langchain_chroma import Chroma  # New import
except ImportError:
    from langchain_community.vectorstores import Chroma  # Fallback

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

def build_database(rebuild_from_scratch: bool = False, fetch_web_data: bool = False):
    print("🚀 Starting RAG database build...")
    
    # Fetch fresh web data if requested
    if fetch_web_data:
        try:
            from web_scraper import update_knowledge_base_with_web_data
            print("🌐 Fetching fresh web data...")
            update_knowledge_base_with_web_data()
        except ImportError:
            print("⚠️  Web scraper not available, skipping web data fetch")
        except Exception as e:
            print(f"⚠️  Error fetching web data: {e}")
    
    # Configuration
    knowledge_base_path = "knowledge_base"
    vector_db_path = "vector_db"
    
    # Only remove existing database if rebuilding from scratch
    if rebuild_from_scratch and os.path.exists(vector_db_path):
        shutil.rmtree(vector_db_path)
        print("🗑️  Removed existing vector database (rebuild mode)")
    elif not rebuild_from_scratch and os.path.exists(vector_db_path):
        print("📂 Updating existing vector database (incremental mode)")
    
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
        
        # Create embeddings
        print("🧠 Creating embeddings...")
        embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs={'device': 'cpu'}
        )
        
        # Create or update vector store
        if rebuild_from_scratch or not os.path.exists(vector_db_path):
            print("💾 Building new vector database...")
            # Remove any existing corrupted database first
            if os.path.exists(vector_db_path):
                shutil.rmtree(vector_db_path)
                print("🗑️ Removed existing database for clean rebuild")
            
            vectorstore = Chroma.from_documents(
                documents=splits,
                embedding=embeddings,
                persist_directory=vector_db_path
            )
        else:
            print("➕ Adding to existing vector database...")
            try:
                # Load existing database
                vectorstore = Chroma(
                    persist_directory=vector_db_path,
                    embedding_function=embeddings
                )
                # Test connection before adding documents
                test_count = vectorstore._collection.count()
                print(f"📊 Existing database has {test_count} documents")
                
                # Add new documents
                vectorstore.add_documents(splits)
            except Exception as db_error:
                print(f"❌ Error with existing database: {db_error}")
                print("🔄 Rebuilding database from scratch...")
                
                # Remove corrupted database and rebuild
                if os.path.exists(vector_db_path):
                    shutil.rmtree(vector_db_path)
                    print("🗑️ Removed corrupted database")
                
                vectorstore = Chroma.from_documents(
                    documents=splits,
                    embedding=embeddings,
                    persist_directory=vector_db_path
                )
        
        # Persist the database (newer versions auto-persist)
        try:
            vectorstore.persist()
            print("💾 Database persisted successfully")
        except AttributeError:
            # Newer versions of ChromaDB auto-persist, no need to call persist()
            print("💾 Database auto-persisted (newer ChromaDB version)")
        except Exception as persist_error:
            print(f"⚠️ Persist warning: {persist_error} (continuing anyway)")
        
        print("✅ Vector database updated successfully!")
        
        # Get final count
        try:
            final_count = vectorstore._collection.count()
            print(f"📊 Database now contains {final_count} documents")
        except:
            print("📊 Database updated successfully")
        
        print("🎉 RAG database operation completed!")
        
    except Exception as e:
        print(f"❌ Error updating database: {str(e)}")
        raise

if __name__ == "__main__":
    import sys
    
    # Check for flags
    rebuild = "--rebuild" in sys.argv or "-r" in sys.argv
    fetch_web = "--web" in sys.argv or "-w" in sys.argv
    
    if rebuild:
        print("🔄 Rebuilding database from scratch...")
    else:
        print("➕ Incremental update mode...")
        
    if fetch_web:
        print("🌐 Will fetch fresh web data...")
        
    build_database(rebuild_from_scratch=rebuild, fetch_web_data=fetch_web)