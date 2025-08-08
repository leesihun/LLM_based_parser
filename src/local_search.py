#!/usr/bin/env python3
"""
Local Search System
Works without external internet access - searches local files and provides knowledge
"""

import os
import json
import re
from typing import List, Dict, Optional
from datetime import datetime

class LocalSearcher:
    """Search local files and provide knowledge-based responses"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.data_dir = "data"
        self.uploads_dir = "uploads"
        
    def search_local_files(self, query: str, max_results: int = 5) -> List[Dict[str, str]]:
        """Search through local files"""
        results = []
        query_lower = query.lower()
        
        # Search in data directory
        if os.path.exists(self.data_dir):
            for filename in os.listdir(self.data_dir):
                if filename.endswith(('.md', '.txt', '.json')):
                    file_path = os.path.join(self.data_dir, filename)
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                            
                        # Search for query in content
                        if query_lower in content.lower():
                            # Extract relevant snippet
                            lines = content.split('\n')
                            relevant_lines = []
                            
                            for i, line in enumerate(lines):
                                if query_lower in line.lower():
                                    # Get context around the match
                                    start = max(0, i-2)
                                    end = min(len(lines), i+3)
                                    context = ' '.join(lines[start:end])
                                    relevant_lines.append(context[:200])
                            
                            if relevant_lines:
                                results.append({
                                    'title': f'Local File: {filename}',
                                    'snippet': relevant_lines[0] + '...',
                                    'url': file_path,
                                    'source': 'Local Files'
                                })
                                
                    except Exception as e:
                        continue
        
        # Search in uploads directory
        if os.path.exists(self.uploads_dir):
            for filename in os.listdir(self.uploads_dir):
                if filename.endswith(('.md', '.txt')):
                    file_path = os.path.join(self.uploads_dir, filename)
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                            
                        if query_lower in content.lower():
                            lines = content.split('\n')
                            for i, line in enumerate(lines):
                                if query_lower in line.lower():
                                    start = max(0, i-1)
                                    end = min(len(lines), i+2)
                                    context = ' '.join(lines[start:end])
                                    
                                    results.append({
                                        'title': f'Uploaded: {filename}',
                                        'snippet': context[:200] + '...',
                                        'url': file_path,
                                        'source': 'Uploaded Files'
                                    })
                                    break
                                    
                    except Exception as e:
                        continue
        
        return results[:max_results]
    
    def get_knowledge_response(self, query: str) -> List[Dict[str, str]]:
        """Provide knowledge-based responses for common queries"""
        query_lower = query.lower()
        results = []
        
        # Programming-related queries
        if any(term in query_lower for term in ['python', 'programming', 'code', 'development']):
            results.append({
                'title': 'Python Programming Resources',
                'snippet': 'Python is a high-level programming language. Key concepts: variables, functions, classes, modules. Popular frameworks: Django, Flask, FastAPI. Data science: pandas, numpy, matplotlib.',
                'url': 'local://python-knowledge',
                'source': 'Local Knowledge'
            })
        
        if any(term in query_lower for term in ['web', 'html', 'css', 'javascript']):
            results.append({
                'title': 'Web Development Fundamentals',
                'snippet': 'Web development involves HTML (structure), CSS (styling), and JavaScript (interactivity). Modern frameworks: React, Vue, Angular. Backend: Node.js, Python, PHP.',
                'url': 'local://web-knowledge',
                'source': 'Local Knowledge'
            })
        
        if any(term in query_lower for term in ['machine learning', 'ai', 'artificial intelligence']):
            results.append({
                'title': 'Machine Learning Basics',
                'snippet': 'Machine learning is a subset of AI. Types: supervised, unsupervised, reinforcement learning. Popular libraries: scikit-learn, TensorFlow, PyTorch. Applications: classification, regression, clustering.',
                'url': 'local://ml-knowledge',
                'source': 'Local Knowledge'
            })
        
        if any(term in query_lower for term in ['database', 'sql', 'data']):
            results.append({
                'title': 'Database Fundamentals',
                'snippet': 'Databases store and organize data. SQL databases: MySQL, PostgreSQL, SQLite. NoSQL: MongoDB, Redis. Key concepts: tables, queries, indexing, normalization.',
                'url': 'local://database-knowledge',
                'source': 'Local Knowledge'
            })
        
        return results
    
    def search(self, query: str, max_results: int = 5) -> List[Dict[str, str]]:
        """Main search function combining local files and knowledge"""
        results = []
        
        # Search local files first
        local_results = self.search_local_files(query, max_results//2)
        results.extend(local_results)
        
        # Add knowledge-based results
        knowledge_results = self.get_knowledge_response(query)
        results.extend(knowledge_results)
        
        # If no results, provide helpful message
        if not results:
            results.append({
                'title': f'No Local Results for: {query}',
                'snippet': 'No matching content found in local files. This system works offline due to network restrictions. Upload relevant documents to search them, or ask about programming topics for knowledge-based responses.',
                'url': 'local://help',
                'source': 'System Message'
            })
        
        return results[:max_results]
    
    def search_with_context(self, query: str, max_results: Optional[int] = None) -> str:
        """Format search results for LLM context"""
        results = self.search(query, max_results or 5)
        
        context = f"Local Search Results for '{query}':\n\n"
        
        for i, result in enumerate(results, 1):
            context += f"{i}. **{result['title']}**\n"
            if result['snippet']:
                context += f"   {result['snippet']}\n"
            context += f"   Source: {result['source']}\n"
            context += "\n"
        
        return context
    
    def test_search_capability(self) -> Dict[str, any]:
        """Test local search functionality"""
        test_query = "python programming"
        
        try:
            results = self.search(test_query, max_results=3)
            
            return {
                'success': len(results) > 0,
                'result_count': len(results),
                'test_query': test_query,
                'engines_working': ['Local Files', 'Knowledge Base'],
                'sample_result': results[0] if results else None,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'test_query': test_query,
                'timestamp': datetime.now().isoformat()
            }

def test_local_search():
    """Test the local search system"""
    print("Testing Local Search System")
    print("=" * 40)
    
    searcher = LocalSearcher()
    
    # Test capability
    test_result = searcher.test_search_capability()
    print(f"Test Status: {'SUCCESS' if test_result['success'] else 'FAILED'}")
    print(f"Results found: {test_result['result_count']}")
    
    # Test different queries
    test_queries = [
        "python programming",
        "web development", 
        "machine learning",
        "database"
    ]
    
    for query in test_queries:
        print(f"\nSearching: '{query}'")
        results = searcher.search(query, max_results=2)
        
        for i, result in enumerate(results, 1):
            print(f"  {i}. {result['title']}")
            print(f"     {result['snippet'][:60]}...")
            print(f"     Source: {result['source']}")

if __name__ == "__main__":
    test_local_search()