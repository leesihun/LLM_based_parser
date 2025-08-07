# Implementation Plan for Enhanced LLM Query System

## Goal
Enable the system to answer counting, keyword extraction, and topic-specific queries that traditional RAG cannot handle effectively.

## Problem Analysis

Traditional RAG limitations for these query types:

1. **"How many positive reviews are there?"**
   - **Type**: COUNT query across entire dataset
   - **RAG Issue**: Only returns top-k relevant docs, not ALL positive reviews
   - **Need**: Direct dataset statistics

2. **"What are top 100 positive keywords regarding the given phone?"** 
   - **Type**: KEYWORD EXTRACTION + FREQUENCY ANALYSIS
   - **RAG Issue**: Doesn't perform statistical analysis across all positive reviews
   - **Need**: NLP processing of entire positive review subset

3. **"How many negative reviews are there regarding battery life?"**
   - **Type**: COUNT + TOPIC FILTERING
   - **RAG Issue**: Semantic search may miss relevant docs, no guarantee of complete coverage
   - **Need**: Topic classification + counting across entire negative review subset

## Proposed Solution Architecture

### Hybrid System Components

1. **Dataset Analyzer** (`src/dataset_analyzer.py`)
   - Direct access to all documents for counting operations
   - Sentiment-based filtering and statistics
   - Handle queries like "How many positive reviews?"

2. **Topic Classifier** (`src/topic_classifier.py`) 
   - Classify reviews by topics (battery, screen, camera, performance, etc.)
   - Enable filtering like "reviews about battery life"
   - Use keyword-based or semantic classification

3. **Keyword Extractor** (`src/keyword_extractor.py`)
   - NLP processing with spaCy/NLTK for keyword extraction
   - TF-IDF analysis for ranking keyword importance
   - Handle queries like "top 100 positive keywords"

4. **Query Router** (`src/query_router.py`)
   - Classify query types: COUNT, KEYWORD_EXTRACTION, TOPIC_FILTER, SEMANTIC_SEARCH
   - Route queries to appropriate processing modules
   - Use pattern matching for query classification

5. **Hybrid Query Engine** (`src/query_engine.py`)
   - Orchestrate multiple processing approaches
   - Combine results from RAG + dataset analysis
   - Handle complex multi-step queries

### Query Processing Flow
```
User Query 
    ↓
Query Router (classify query type)
    ↓
┌─────────────────────────────────────────┐
│ Route to appropriate processing module: │
├─ COUNT queries → Dataset Analyzer       │
├─ KEYWORD queries → Keyword Extractor    │  
├─ TOPIC+COUNT → Topic Classifier + Count │
└─ SEMANTIC queries → RAG System          │
└─────────────────────────────────────────┘
    ↓
Query Engine (combine results)
    ↓
Return structured answer
```

### Example Query Routing
- **"How many positive reviews?"** → `COUNT` + `SENTIMENT_FILTER(positive)`
- **"Top 100 positive keywords"** → `KEYWORD_EXTRACTION` + `SENTIMENT_FILTER(positive)` 
- **"How many negative reviews about battery?"** → `TOPIC_FILTER(battery)` + `COUNT` + `SENTIMENT_FILTER(negative)`
- **"What do users think about camera quality?"** → `RAG semantic search`

## Implementation Phases

### Phase 1: Dataset Analyzer
- Create `src/dataset_analyzer.py`
- Implement sentiment counting functionality
- Add basic dataset statistics
- Handle queries: "How many positive/negative reviews?"

### Phase 2: Topic Classifier
- Create `src/topic_classifier.py` 
- Define topic categories (battery, screen, camera, performance, etc.)
- Implement keyword-based topic detection
- Enable topic-based filtering

### Phase 3: Keyword Extractor
- Create `src/keyword_extractor.py`
- Add NLP dependencies (spaCy, scikit-learn)
- Implement TF-IDF analysis
- Extract and rank keywords by sentiment
- Handle queries: "top N positive/negative keywords"

### Phase 4: Query Router
- Create `src/query_router.py`
- Implement query type classification
- Add pattern matching for common query types
- Route queries to appropriate modules

### Phase 5: Hybrid Query Engine
- Create `src/query_engine.py`
- Orchestrate multiple processing modules
- Combine results from different sources
- Handle complex multi-step queries

### Phase 6: Interface Updates
- Update CLI to use hybrid query engine
- Update Streamlit interface
- Add query type indicators
- Improve result presentation

## Dependencies to Add

```bash
# For keyword extraction and NLP
pip install spacy scikit-learn nltk

# Download spaCy model
python -m spacy download en_core_web_sm
```

## File Structure After Implementation

```
src/
├── excel_reader.py          # Existing
├── rag_system.py            # Existing  
├── ollama_client.py         # Existing
├── main.py                  # Existing
├── dataset_analyzer.py      # NEW - counting and statistics
├── topic_classifier.py      # NEW - topic detection and filtering
├── keyword_extractor.py     # NEW - keyword extraction and ranking
├── query_router.py          # NEW - query type classification
└── query_engine.py          # NEW - hybrid query orchestration
```

This hybrid approach enables the LLM to handle both traditional RAG queries AND the specialized counting/analysis queries required.