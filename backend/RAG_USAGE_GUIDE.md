# RAG Database Usage Guide

## How the RAG System Works

The RAG (Retrieval-Augmented Generation) system processes your knowledge base in the following way:

### 1. Static Content (Current Default)
- Reads files from `knowledge_base/` folder
- Processes `.txt` and `.pdf` files
- Creates vector embeddings from text content
- Stores in ChromaDB vector database

### 2. Dynamic Web Content (New Feature)
- Optionally fetches live data from web sources
- Downloads current SonarSource security rules
- Updates knowledge base with fresh data
- Then processes as normal

## Usage Commands

### Basic RAG Database Build
```bash
python build_rag_db.py
```

### Rebuild from Scratch
```bash
python build_rag_db.py --rebuild
# or
python build_rag_db.py -r
```

### Fetch Fresh Web Data
```bash
python build_rag_db.py --web
# or
python build_rag_db.py -w
```

### Rebuild with Fresh Web Data
```bash
python build_rag_db.py --rebuild --web
# or
python build_rag_db.py -r -w
```

## What Happens with Links

### Static Links (like sonar_security_rules.txt)
- ✅ The URL and description text are indexed
- ✅ RAG can reference the link and explain what it contains
- ❌ Does NOT automatically fetch live content from the URL
- ❌ Cannot provide real-time data from the website

### Dynamic Web Scraping (with --web flag)
- ✅ Actually visits the websites
- ✅ Downloads current data
- ✅ Saves to knowledge base files
- ✅ Then indexes the live content
- ✅ Provides up-to-date information

## Example Workflow

1. **Initial Setup**: Run with static content
   ```bash
   python build_rag_db.py --rebuild
   ```

2. **Weekly Updates**: Fetch fresh web data
   ```bash
   python build_rag_db.py --web
   ```

3. **Major Rebuild**: Complete refresh with web data
   ```bash
   python build_rag_db.py --rebuild --web
   ```

## When to Use Each Mode

### Static Mode (Default)
- Quick builds
- Offline usage
- When web sources haven't changed
- Development/testing

### Web Scraping Mode (--web flag)
- Need current vulnerability data
- Weekly/monthly knowledge base updates
- Production deployments
- When accuracy with latest info is critical

## Important Notes

1. **Rate Limiting**: Web scraping is rate-limited to be respectful to source websites
2. **Error Handling**: If web scraping fails, the system continues with existing static content
3. **Storage**: Web data is saved to files first, then processed like normal documents
4. **Updates**: Use incremental mode for faster updates, rebuild for clean slate
