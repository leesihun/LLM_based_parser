"""Command-line interface for the LLM-based parser."""

import argparse
import sys
from pathlib import Path

# Add src to Python path
sys.path.append(str(Path(__file__).parent / "src"))

from excel_reader import ExcelReader
from rag_system import RAGSystem
from config.config import config
import ollama


def setup_rag_system():
    """Initialize and populate RAG system with data."""
    print("🚀 Initializing RAG system...")
    
    # Initialize components
    excel_reader = ExcelReader()  # Uses config defaults
    rag_system = RAGSystem(
        collection_name=config.rag_collection_name,
        embedding_model=config.embedding_model,
        persist_directory=str(config.chromadb_dir)
    )
    
    # Load data using new detailed format
    print("📊 Loading review data with detailed metadata...")
    detailed_documents = excel_reader.get_detailed_documents()
    
    if not detailed_documents:
        print(f"❌ No review data found. Please ensure {config.positive_filename} and {config.negative_filename} exist in data/ directory.")
        return False
    
    # Show detailed statistics
    total_chars = sum(len(doc["text"]) for doc in detailed_documents)
    avg_chars = total_chars / len(detailed_documents)
    sentiments = {}
    for doc in detailed_documents:
        sentiment = doc["metadata"]["sentiment"]
        sentiments[sentiment] = sentiments.get(sentiment, 0) + 1
    
    print(f"📈 Dataset Statistics:")
    print(f"   Total documents: {len(detailed_documents)}")
    print(f"   Average document length: {avg_chars:.0f} characters")
    print(f"   Sentiment distribution: {dict(sentiments)}")
    print(f"   Total context size: {total_chars:,} characters")
    
    # Add to RAG system
    print(f"🔄 Processing {len(detailed_documents)} detailed documents...")
    rag_system.clear_collection()
    rag_system.add_documents(detailed_documents)
    
    print(f"✅ Successfully loaded {len(detailed_documents)} detailed documents into RAG system")
    return True


def query_mode():
    """Interactive query mode using direct Ollama client like setup does."""
    print("💬 Entering interactive query mode...")
    print("Type 'quit' or 'exit' to stop\n")
    
    # Initialize components - use same approach as setup_rag_system
    rag_system = RAGSystem(
        collection_name=config.rag_collection_name,
        embedding_model=config.embedding_model,
        persist_directory=str(config.chromadb_dir)
    )
    
    # Use direct Ollama client like RAGSystem does (same as setup)
    ollama_host = f"http://{config.ollama_host}"
    ollama_client = ollama.Client(host=ollama_host, timeout=config.ollama_timeout)
    model_name = config.default_ollama_model
    
    print(f"🤖 Using model: {model_name}")
    print(f"🔗 Ollama host: {ollama_host}\n")
    
    while True:
        try:
            query = input("❓ Enter your question: ").strip()
            
            if query.lower() in ['quit', 'exit', 'q']:
                break
            
            if not query:
                continue
            
            print("\n🔍 Searching relevant reviews...")
            
            # Get detailed results instead of just formatted context
            rag_results = rag_system.query(query, config.rag_context_size)
            
            print(f"📋 Found {len(rag_results['documents'])} relevant documents:")
            for i, (doc, distance, metadata) in enumerate(zip(rag_results['documents'], rag_results['distances'], rag_results['metadatas'])):
                similarity = 1 - distance
                sentiment = metadata.get('sentiment', 'unknown')
                source = metadata.get('file_source', 'unknown')
                row_idx = metadata.get('row_index', 'unknown')
                doc_length = metadata.get('document_length', len(doc))
                
                print(f"  {i+1}. Similarity: {similarity:.3f} | {sentiment.upper()} | {source} row {row_idx} | {doc_length} chars")
                print(f"      Preview: {doc[:150]}...")
            
            # Format context for LLM - include ALL retrieved documents
            if rag_results['documents']:
                context_parts = []
                for i, doc in enumerate(rag_results['documents']):
                    context_parts.append(f"Review {i+1}: {doc}")
                context = "\n\n".join(context_parts)
                print(f"\n📄 Context includes {len(rag_results['documents'])} reviews, {len(context):,} characters total")
                
                # Show sentiment distribution of retrieved docs
                sentiments = {}
                for metadata in rag_results['metadatas']:
                    sentiment = metadata.get('sentiment', 'unknown')
                    sentiments[sentiment] = sentiments.get(sentiment, 0) + 1
                print(f"📊 Retrieved sentiment distribution: {dict(sentiments)}")
            else:
                context = "No relevant reviews found."
                print("\n⚠️ No relevant context found!")
                
            # Show distances for debugging
            if rag_results['distances']:
                min_dist = min(rag_results['distances'])
                max_dist = max(rag_results['distances'])
                avg_dist = sum(rag_results['distances']) / len(rag_results['distances'])
                print(f"📊 Distance stats - Min: {min_dist:.3f}, Max: {max_dist:.3f}, Avg: {avg_dist:.3f}")
            
            print("\n🤖 Generating response...")
            
            # Use direct Ollama client like RAGSystem does - same method as setup
            # Detect language (same logic as OllamaClient had)
            korean_chars = sum(1 for char in query if '\uac00' <= char <= '\ud7a3')
            total_chars = len([c for c in query if c.isalpha()])
            language = "ko" if korean_chars > total_chars * 0.3 else "en"
            
            # System prompts
            system_prompts = {
                "en": """You are an AI assistant specialized in analyzing cellphone reviews. 
You have access to a database of positive and negative cellphone reviews, specifically about foldable phones.

Use the provided context to answer questions accurately. If the context doesn't contain 
relevant information, say so clearly. Focus on insights from the review data.

Context format: Reviews are tagged with [POSITIVE] or [NEGATIVE] to indicate sentiment.""",
                
                "ko": """당신은 휴대폰 리뷰 분석 전문 AI 어시스턴트입니다.
폴더블 폰에 대한 긍정적, 부정적 리뷰 데이터베이스에 접근할 수 있습니다.

제공된 맥락을 사용하여 질문에 정확하게 답변하세요. 맥락에 관련 정보가 없다면 명확히 말씀해 주세요. 
리뷰 데이터의 인사이트에 집중하세요.

맥락 형식: 리뷰는 감정을 나타내기 위해 [POSITIVE] 또는 [NEGATIVE]로 태그가 지정됩니다."""
            }
            
            # Prompts
            prompt_templates = {
                "en": """Based on the following context from cellphone reviews, please answer the user's question.

Context:
{context}

Question: {query}

Please provide a helpful and accurate answer based on the review data provided.""",
                
                "ko": """다음 휴대폰 리뷰 맥락을 바탕으로 사용자의 질문에 답변해 주세요.

맥락:
{context}

질문: {query}

제공된 리뷰 데이터를 바탕으로 도움이 되고 정확한 답변을 제공해 주세요."""
            }
            
            system_prompt = system_prompts.get(language, system_prompts["en"])
            prompt_template = prompt_templates.get(language, prompt_templates["en"])
            prompt = prompt_template.format(context=context, query=query)
            
            # Show what we're sending to the LLM for debugging
            print(f"🔤 Language detected: {language}")
            print(f"📤 Sending to LLM:")
            print(f"  System prompt: {system_prompt[:100]}...")
            print(f"  User prompt length: {len(prompt)} characters")
            print(f"  First 200 chars of prompt: {prompt[:200]}...")
            
            # Generate response using direct Ollama client (same as setup uses)
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ]
            
            response = ollama_client.chat(
                model=model_name,
                messages=messages,
                options={
                    "temperature": 0.3,
                    "num_predict": config.max_tokens
                }
            )
            
            response_text = response['message']['content']
            print(f"\n💬 Response:\n{response_text}\n")
            print("-" * 80)
            
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n👋 Goodbye!")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="LLM-based Parser for Cellphone Reviews",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python cli.py setup          # Initialize RAG system with review data
  python cli.py query          # Start interactive query mode
  python cli.py status         # Show system status
        """
    )
    
    parser.add_argument(
        'command',
        choices=['setup', 'query', 'status'],
        help='Command to execute'
    )
    
    parser.add_argument(
        '--model',
        type=str,
        help='Specify Ollama model to use'
    )
    
    args = parser.parse_args()
    
    # Update default model if specified
    if args.model:
        config.default_ollama_model = args.model
    
    if args.command == 'setup':
        success = setup_rag_system()
        sys.exit(0 if success else 1)
    
    elif args.command == 'query':
        query_mode()
    
    elif args.command == 'status':
        print("📊 System Status:")
        print(f"Config: {config.to_dict()}")
        print(f"Files: {config.get_file_status()}")


if __name__ == "__main__":
    main()