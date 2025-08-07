"""Main application for the LLM-based parser with RAG system."""

import streamlit as st
import logging
from pathlib import Path
import sys

# Add src to Python path
sys.path.append(str(Path(__file__).parent))

from excel_reader import ExcelReader
from rag_system import RAGSystem
from ollama_client import OllamaClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LLMParser:
    """Main application class for LLM-based parser."""
    
    def __init__(self):
        self.excel_reader = None
        self.rag_system = None
        self.ollama_client = None
        self.initialized = False
    
    def initialize_components(self):
        """Initialize all system components."""
        try:
            # Initialize components
            self.excel_reader = ExcelReader()
            self.rag_system = RAGSystem()
            self.ollama_client = OllamaClient()
            
            logger.info("All components initialized successfully")
            self.initialized = True
            return True
            
        except Exception as e:
            logger.error(f"Error initializing components: {e}")
            st.error(f"Failed to initialize system: {e}")
            return False
    
    def load_data_to_rag(self):
        """Load Excel data into RAG system."""
        try:
            # Get review texts from Excel files
            review_texts = self.excel_reader.get_review_texts()
            
            if not review_texts:
                st.warning("No review data found. Please ensure fold_positive.xlsx and fold_negative.xlsx exist in the data/ directory.")
                return False
            
            # Clear existing data and add new data
            self.rag_system.clear_collection()
            self.rag_system.add_documents(review_texts)
            
            st.success(f"Successfully loaded {len(review_texts)} reviews into RAG system")
            return True
            
        except Exception as e:
            logger.error(f"Error loading data to RAG: {e}")
            st.error(f"Failed to load data: {e}")
            return False
    
    def query_system(self, user_query: str, selected_model: str, language: str = "auto") -> str:
        """Query the system with RAG-enhanced LLM."""
        try:
            # Get relevant context from RAG
            context = self.rag_system.get_context_for_query(user_query)
            
            # Generate response using Ollama
            response = self.ollama_client.generate_with_context(
                query=user_query,
                context=context,
                model=selected_model,
                language=language
            )
            
            return response or "Sorry, I couldn't generate a response. Please try again."
            
        except Exception as e:
            logger.error(f"Error querying system: {e}")
            return f"Error processing query: {e}"


def main():
    """Main Streamlit application."""
    st.set_page_config(
        page_title="Cellphone Review Analyzer",
        page_icon="📱",
        layout="wide"
    )
    
    st.title("📱 Cellphone Review Analyzer")
    st.markdown("An LLM-powered system for analyzing cellphone reviews using RAG")
    
    # Initialize session state
    if 'parser' not in st.session_state:
        st.session_state.parser = LLMParser()
    
    if 'initialized' not in st.session_state:
        st.session_state.initialized = False
    
    # Sidebar for configuration
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # Initialize system button
        if st.button("🚀 Initialize System", type="primary"):
            with st.spinner("Initializing components..."):
                success = st.session_state.parser.initialize_components()
                if success:
                    st.session_state.initialized = True
                    st.success("System initialized!")
        
        # Load data button
        if st.session_state.initialized:
            if st.button("📊 Load Review Data"):
                with st.spinner("Loading review data into RAG system..."):
                    st.session_state.parser.load_data_to_rag()
            
            # Model selection
            st.header("🤖 Model Selection")
            available_models = st.session_state.parser.ollama_client.get_available_models()
            
            if available_models:
                selected_model = st.selectbox(
                    "Choose Ollama Model:",
                    available_models,
                    index=0
                )
            else:
                st.warning("No Ollama models found. Please install models using 'ollama pull <model_name>'")
                selected_model = st.text_input("Enter model name manually:", value="qwen2")
            
            # Language selection
            st.header("🌐 Language")
            language_options = {
                "Auto Detect": "auto",
                "English": "en", 
                "한국어": "ko"
            }
            selected_language_label = st.selectbox(
                "Response Language:",
                list(language_options.keys()),
                index=0
            )
            selected_language = language_options[selected_language_label]
            
            # RAG system stats
            if hasattr(st.session_state.parser, 'rag_system') and st.session_state.parser.rag_system:
                stats = st.session_state.parser.rag_system.get_collection_stats()
                st.metric("Documents in RAG", stats.get('document_count', 0))
    
    # Main interface
    if not st.session_state.initialized:
        st.info("👈 Please initialize the system using the sidebar")
        st.markdown("""
        ### Getting Started:
        1. Click "Initialize System" in the sidebar
        2. Place your Excel files (`fold_positive.xlsx` and `fold_negative.xlsx`) in the `data/` directory
        3. Click "Load Review Data" to index the reviews
        4. Select your preferred Ollama model
        5. Start asking questions about the cellphone reviews!
        """)
    else:
        # Chat interface
        st.header("💬 Chat with Review Data")
        
        # Query input with Korean example
        placeholder_text = {
            "auto": "e.g., What are the main positive aspects of foldable phones? / 폴더블 폰의 주요 장점은 무엇인가요?",
            "en": "e.g., What are the main positive aspects of foldable phones?",
            "ko": "예: 폴더블 폰의 주요 장점은 무엇인가요?"
        }.get(selected_language, "Ask a question about the cellphone reviews...")
        
        user_query = st.text_input(
            "Ask a question about the cellphone reviews:",
            placeholder=placeholder_text
        )
        
        # Query button
        if st.button("🔍 Ask Question") and user_query:
            if not hasattr(st.session_state.parser, 'rag_system') or not st.session_state.parser.rag_system:
                st.error("Please load review data first!")
            else:
                with st.spinner("Generating response..."):
                    response = st.session_state.parser.query_system(user_query, selected_model, selected_language)
                    
                    # Display response
                    st.markdown("### 🤖 Response:")
                    st.markdown(response)
        
        # Chat history (basic implementation)
        if 'chat_history' not in st.session_state:
            st.session_state.chat_history = []
        
        if user_query and st.button("💾 Save to History"):
            st.session_state.chat_history.append({
                'query': user_query,
                'response': response if 'response' in locals() else "No response generated"
            })
        
        # Display chat history
        if st.session_state.chat_history:
            st.header("📚 Chat History")
            for i, chat in enumerate(reversed(st.session_state.chat_history[-5:])):  # Show last 5
                with st.expander(f"Q: {chat['query'][:50]}..."):
                    st.markdown(f"**Query:** {chat['query']}")
                    st.markdown(f"**Response:** {chat['response']}")


if __name__ == "__main__":
    main()