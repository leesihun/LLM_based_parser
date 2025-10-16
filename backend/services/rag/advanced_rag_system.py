#!/usr/bin/env python3
"""
Advanced RAG System
Enhanced retrieval-augmented generation with multi-document intelligence,
relationship mapping, and knowledge graph capabilities
"""

import os
import json
import logging
import hashlib
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Set
from datetime import datetime
import re
from collections import defaultdict, Counter
import math

# Disable ChromaDB telemetry
os.environ["ANONYMIZED_TELEMETRY"] = "False"

try:
    import chromadb
    from chromadb.api.types import EmbeddingFunction, Embeddings
    HAS_CHROMADB = True
except ImportError:
    HAS_CHROMADB = False

try:
    import numpy as np
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    from sklearn.cluster import KMeans
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False

try:
    import networkx as nx
    HAS_NETWORKX = True
except ImportError:
    HAS_NETWORKX = False


class DocumentRelationshipAnalyzer:
    """Analyzes relationships between documents"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # Document similarity threshold
        self.similarity_threshold = self.config.get('similarity_threshold', 0.3)
        
        # Entity extraction patterns
        self.entity_patterns = {
            'person': r'\b[A-Z][a-z]+ [A-Z][a-z]+\b',
            'organization': r'\b[A-Z][A-Za-z\s]{2,30}(?:Inc|Corp|Ltd|LLC|Company|Organization)\b',
            'location': r'\b[A-Z][a-z]+(?: [A-Z][a-z]+)* (?:City|State|Country|Street|Avenue|Road)\b',
            'date': r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b|\b\d{4}[/-]\d{1,2}[/-]\d{1,2}\b',
            'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            'phone': r'\b(?:\+?1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}\b',
            'url': r'https?://[^\s<>"{\}|\\^`\[\]]+'
        }
    
    def analyze_document_relationships(self, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze relationships between multiple documents
        
        Args:
            documents: List of document dictionaries with content and metadata
            
        Returns:
            Analysis results with relationships, clusters, and insights
        """
        try:
            if not HAS_SKLEARN:
                return {'error': 'Advanced analytics not available - sklearn required'}
            
            if len(documents) < 2:
                return {'error': 'Need at least 2 documents for relationship analysis'}
            
            analysis = {
                'total_documents': len(documents),
                'relationships': [],
                'document_clusters': [],
                'shared_entities': {},
                'content_overlap': [],
                'knowledge_gaps': [],
                'timestamp': datetime.now().isoformat()
            }
            
            # Extract content and metadata
            doc_contents = [doc.get('content', '') for doc in documents]
            doc_ids = [doc.get('id', f'doc_{i}') for i, doc in enumerate(documents)]
            
            # Calculate document similarities
            analysis['relationships'] = self._calculate_document_similarities(doc_contents, doc_ids)
            
            # Cluster documents by similarity
            analysis['document_clusters'] = self._cluster_documents(doc_contents, doc_ids)
            
            # Find shared entities across documents
            analysis['shared_entities'] = self._find_shared_entities(documents)
            
            # Analyze content overlap
            analysis['content_overlap'] = self._analyze_content_overlap(documents)
            
            # Identify knowledge gaps
            analysis['knowledge_gaps'] = self._identify_knowledge_gaps(documents)
            
            # Generate insights
            analysis['insights'] = self._generate_relationship_insights(analysis)
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"Error analyzing document relationships: {str(e)}")
            return {'error': str(e)}
    
    def _calculate_document_similarities(self, contents: List[str], doc_ids: List[str]) -> List[Dict[str, Any]]:
        """Calculate pairwise document similarities"""
        try:
            # Use TF-IDF for similarity calculation
            vectorizer = TfidfVectorizer(
                max_features=1000,
                stop_words='english',
                ngram_range=(1, 2)
            )
            
            tfidf_matrix = vectorizer.fit_transform(contents)
            similarity_matrix = cosine_similarity(tfidf_matrix)
            
            relationships = []
            for i in range(len(contents)):
                for j in range(i + 1, len(contents)):
                    similarity = similarity_matrix[i][j]
                    if similarity > self.similarity_threshold:
                        relationships.append({
                            'doc1_id': doc_ids[i],
                            'doc2_id': doc_ids[j],
                            'similarity_score': float(similarity),
                            'relationship_type': self._classify_relationship_type(similarity),
                            'shared_terms': self._find_shared_terms(contents[i], contents[j], vectorizer)
                        })
            
            # Sort by similarity score
            relationships.sort(key=lambda x: x['similarity_score'], reverse=True)
            return relationships[:20]  # Top 20 relationships
            
        except Exception as e:
            self.logger.error(f"Error calculating similarities: {str(e)}")
            return []
    
    def _cluster_documents(self, contents: List[str], doc_ids: List[str]) -> List[Dict[str, Any]]:
        """Cluster documents by content similarity"""
        try:
            if len(contents) < 3:
                return []  # Need at least 3 documents for meaningful clustering
            
            vectorizer = TfidfVectorizer(
                max_features=500,
                stop_words='english',
                ngram_range=(1, 2)
            )
            
            tfidf_matrix = vectorizer.fit_transform(contents)
            
            # Determine optimal number of clusters (max 5)
            n_clusters = min(5, max(2, len(contents) // 3))
            
            kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
            cluster_labels = kmeans.fit_predict(tfidf_matrix)
            
            # Group documents by cluster
            clusters = defaultdict(list)
            for doc_id, label in zip(doc_ids, cluster_labels):
                clusters[label].append(doc_id)
            
            # Create cluster analysis
            cluster_analysis = []
            feature_names = vectorizer.get_feature_names_out()
            
            for cluster_id, doc_list in clusters.items():
                if len(doc_list) > 1:  # Only include clusters with multiple documents
                    # Get cluster centroid keywords
                    cluster_indices = [i for i, label in enumerate(cluster_labels) if label == cluster_id]
                    cluster_center = np.mean(tfidf_matrix[cluster_indices].toarray(), axis=0)
                    top_features_idx = cluster_center.argsort()[-10:][::-1]
                    keywords = [feature_names[idx] for idx in top_features_idx]
                    
                    cluster_analysis.append({
                        'cluster_id': int(cluster_id),
                        'document_count': len(doc_list),
                        'documents': doc_list,
                        'keywords': keywords,
                        'theme': self._generate_cluster_theme(keywords)
                    })
            
            return cluster_analysis
            
        except Exception as e:
            self.logger.error(f"Error clustering documents: {str(e)}")
            return []
    
    def _find_shared_entities(self, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Find entities shared across multiple documents"""
        try:
            entity_documents = defaultdict(set)
            all_entities = defaultdict(set)
            
            for i, doc in enumerate(documents):
                content = doc.get('content', '')
                doc_id = doc.get('id', f'doc_{i}')
                
                # Extract entities using patterns
                for entity_type, pattern in self.entity_patterns.items():
                    matches = re.findall(pattern, content, re.IGNORECASE)
                    for match in matches:
                        normalized_match = match.lower().strip()
                        if len(normalized_match) > 2:  # Filter out very short matches
                            entity_documents[normalized_match].add(doc_id)
                            all_entities[entity_type].add(normalized_match)
            
            # Find entities that appear in multiple documents
            shared_entities = {}
            for entity, docs in entity_documents.items():
                if len(docs) > 1:
                    entity_type = self._classify_entity_type(entity)
                    if entity_type not in shared_entities:
                        shared_entities[entity_type] = []
                    
                    shared_entities[entity_type].append({
                        'entity': entity,
                        'document_count': len(docs),
                        'documents': list(docs)
                    })
            
            # Sort by frequency
            for entity_type in shared_entities:
                shared_entities[entity_type].sort(key=lambda x: x['document_count'], reverse=True)
                shared_entities[entity_type] = shared_entities[entity_type][:10]  # Top 10 per type
            
            return shared_entities
            
        except Exception as e:
            self.logger.error(f"Error finding shared entities: {str(e)}")
            return {}
    
    def _analyze_content_overlap(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyze content overlap between documents"""
        try:
            overlaps = []
            
            for i, doc1 in enumerate(documents):
                for j, doc2 in enumerate(documents[i+1:], i+1):
                    content1 = doc1.get('content', '').lower()
                    content2 = doc2.get('content', '').lower()
                    
                    # Find common sentences (simplified)
                    sentences1 = set(sent.strip() for sent in re.split(r'[.!?]+', content1) if len(sent.strip()) > 20)
                    sentences2 = set(sent.strip() for sent in re.split(r'[.!?]+', content2) if len(sent.strip()) > 20)
                    
                    common_sentences = sentences1.intersection(sentences2)
                    
                    if common_sentences:
                        overlap_ratio = len(common_sentences) / max(len(sentences1), len(sentences2))
                        
                        overlaps.append({
                            'doc1_id': doc1.get('id', f'doc_{i}'),
                            'doc2_id': doc2.get('id', f'doc_{j}'),
                            'common_sentences': list(common_sentences)[:5],  # Top 5
                            'overlap_ratio': overlap_ratio,
                            'overlap_type': 'high' if overlap_ratio > 0.3 else 'medium' if overlap_ratio > 0.1 else 'low'
                        })
            
            overlaps.sort(key=lambda x: x['overlap_ratio'], reverse=True)
            return overlaps[:10]  # Top 10 overlaps
            
        except Exception as e:
            self.logger.error(f"Error analyzing content overlap: {str(e)}")
            return []
    
    def _identify_knowledge_gaps(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Identify potential knowledge gaps"""
        try:
            gaps = []
            
            # Analyze document topics/themes
            all_content = ' '.join([doc.get('content', '') for doc in documents])
            
            # Find frequently mentioned topics that might need more coverage
            word_freq = Counter(re.findall(r'\b[a-zA-Z]{4,}\b', all_content.lower()))
            
            # Look for incomplete information indicators
            incomplete_indicators = [
                r'need more information',
                r'to be determined',
                r'incomplete',
                r'\[missing\]',
                r'\[todo\]',
                r'under review',
                r'pending',
                r'coming soon'
            ]
            
            for i, doc in enumerate(documents):
                content = doc.get('content', '')
                doc_id = doc.get('id', f'doc_{i}')
                
                # Find incomplete sections
                for pattern in incomplete_indicators:
                    matches = re.findall(f'.{{0,50}}{pattern}.{{0,50}}', content, re.IGNORECASE)
                    for match in matches:
                        gaps.append({
                            'document_id': doc_id,
                            'gap_type': 'incomplete_information',
                            'context': match.strip(),
                            'confidence': 0.8
                        })
            
            # Find questions without answers
            questions = re.findall(r'[^.!]*\?[^.!]*', all_content)
            for question in questions[:5]:  # Limit to 5 questions
                gaps.append({
                    'gap_type': 'unanswered_question',
                    'context': question.strip(),
                    'confidence': 0.6
                })
            
            return gaps[:10]  # Top 10 gaps
            
        except Exception as e:
            self.logger.error(f"Error identifying knowledge gaps: {str(e)}")
            return []
    
    def _classify_relationship_type(self, similarity_score: float) -> str:
        """Classify relationship type based on similarity score"""
        if similarity_score > 0.7:
            return 'very_similar'
        elif similarity_score > 0.5:
            return 'similar'
        elif similarity_score > 0.3:
            return 'related'
        else:
            return 'weakly_related'
    
    def _find_shared_terms(self, content1: str, content2: str, vectorizer) -> List[str]:
        """Find important shared terms between two documents"""
        try:
            # Get TF-IDF vectors for both documents
            tfidf_matrix = vectorizer.transform([content1, content2])
            feature_names = vectorizer.get_feature_names_out()
            
            # Find terms that appear in both documents with high TF-IDF scores
            doc1_scores = tfidf_matrix[0].toarray()[0]
            doc2_scores = tfidf_matrix[1].toarray()[0]
            
            shared_terms = []
            for i, (score1, score2) in enumerate(zip(doc1_scores, doc2_scores)):
                if score1 > 0 and score2 > 0:  # Term appears in both
                    combined_score = score1 * score2
                    shared_terms.append((feature_names[i], combined_score))
            
            # Sort by combined score and return top terms
            shared_terms.sort(key=lambda x: x[1], reverse=True)
            return [term[0] for term in shared_terms[:10]]
            
        except Exception as e:
            self.logger.error(f"Error finding shared terms: {str(e)}")
            return []
    
    def _generate_cluster_theme(self, keywords: List[str]) -> str:
        """Generate a theme description for a document cluster"""
        if not keywords:
            return 'Mixed content'
        
        # Simple theme generation based on keywords
        top_keywords = keywords[:3]
        return f"Documents about {', '.join(top_keywords)}"
    
    def _classify_entity_type(self, entity: str) -> str:
        """Classify entity type based on patterns"""
        for entity_type, pattern in self.entity_patterns.items():
            if re.match(pattern, entity, re.IGNORECASE):
                return entity_type
        return 'other'
    
    def _generate_relationship_insights(self, analysis: Dict[str, Any]) -> List[str]:
        """Generate insights from relationship analysis"""
        insights = []
        
        # Insights from relationships
        if analysis['relationships']:
            high_similarity = [r for r in analysis['relationships'] if r['similarity_score'] > 0.7]
            if high_similarity:
                insights.append(f"Found {len(high_similarity)} document pairs with very high similarity (>70%)")
        
        # Insights from clusters
        if analysis['document_clusters']:
            largest_cluster = max(analysis['document_clusters'], key=lambda x: x['document_count'])
            insights.append(f"Largest document cluster contains {largest_cluster['document_count']} documents about {largest_cluster['theme']}")
        
        # Insights from shared entities
        if analysis['shared_entities']:
            total_shared = sum(len(entities) for entities in analysis['shared_entities'].values())
            insights.append(f"Found {total_shared} entities shared across multiple documents")
        
        # Insights from overlaps
        if analysis['content_overlap']:
            high_overlaps = [o for o in analysis['content_overlap'] if o['overlap_ratio'] > 0.3]
            if high_overlaps:
                insights.append(f"Detected {len(high_overlaps)} document pairs with significant content overlap")
        
        # Insights from gaps
        if analysis['knowledge_gaps']:
            insights.append(f"Identified {len(analysis['knowledge_gaps'])} potential knowledge gaps or incomplete sections")
        
        return insights


class AdvancedRAGSystem:
    """Enhanced RAG system with multi-document intelligence"""
    
    def __init__(self, config_path: str = "backend/config/config.json", base_rag_system=None):
        """
        Initialize advanced RAG system
        
        Args:
            config_path: Path to configuration file
            base_rag_system: Existing RAG system to extend
        """
        self.config_path = config_path
        self.config = self._load_config(config_path)
        self.logger = logging.getLogger(__name__)
        
        # Initialize base RAG system if provided
        self.base_rag = base_rag_system
        
        # Initialize relationship analyzer
        self.relationship_analyzer = DocumentRelationshipAnalyzer(
            self.config.get('relationship_analysis', {})
        )
        
        # Document cache for relationship analysis
        self.document_cache = {}
        self.relationship_cache = {}
        
        # Enhanced search capabilities
        self.search_history = []
        self.user_preferences = {}
        
        self.logger.info("Advanced RAG System initialized")
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from JSON file"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"Error loading config: {str(e)}")
            return {}
    
    def enhanced_search(self, query: str, user_id: str = None, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Enhanced search with relationship analysis and context awareness
        
        Args:
            query: Search query
            user_id: User ID for personalization
            context: Additional context information
            
        Returns:
            Enhanced search results with relationships and insights
        """
        try:
            # Perform base RAG search if available
            base_results = []
            if self.base_rag:
                try:
                    base_search = self.base_rag.search(query)
                    if base_search.get('success'):
                        base_results = base_search.get('results', [])
                except Exception as e:
                    self.logger.warning(f"Base RAG search failed: {str(e)}")
            
            # Enhance results with relationship analysis
            enhanced_results = self._enhance_search_results(base_results, query, user_id, context)
            
            # Add to search history
            self._add_to_search_history(query, enhanced_results, user_id)
            
            # Generate search insights
            insights = self._generate_search_insights(enhanced_results, query)
            
            return {
                'success': True,
                'query': query,
                'results': enhanced_results,
                'insights': insights,
                'relationship_data': self._get_result_relationships(enhanced_results),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Enhanced search failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'query': query
            }
    
    def analyze_document_collection(self, user_id: str = None) -> Dict[str, Any]:
        """
        Analyze the entire document collection for relationships and insights
        
        Args:
            user_id: User ID for scoped analysis
            
        Returns:
            Collection analysis results
        """
        try:
            # Get all documents from base RAG system
            documents = []
            if self.base_rag:
                try:
                    stats = self.base_rag.get_stats()
                    # This is a simplified approach - in a real implementation,
                    # you'd need to retrieve all documents from ChromaDB
                    documents = self._get_all_documents_from_rag()
                except Exception as e:
                    self.logger.warning(f"Could not retrieve documents from base RAG: {str(e)}")
            
            if not documents:
                return {'error': 'No documents available for analysis'}
            
            # Perform relationship analysis
            relationship_analysis = self.relationship_analyzer.analyze_document_relationships(documents)
            
            # Cache results
            cache_key = f"collection_analysis_{user_id or 'global'}"
            self.relationship_cache[cache_key] = {
                'analysis': relationship_analysis,
                'timestamp': datetime.now().isoformat()
            }
            
            # Generate collection insights
            collection_insights = self._generate_collection_insights(relationship_analysis)
            
            return {
                'success': True,
                'analysis': relationship_analysis,
                'collection_insights': collection_insights,
                'document_count': len(documents),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Collection analysis failed: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_document_suggestions(self, current_doc_id: str, user_id: str = None) -> Dict[str, Any]:
        """
        Get document suggestions based on current document and relationships
        
        Args:
            current_doc_id: Current document ID
            user_id: User ID for personalization
            
        Returns:
            Document suggestions with relationship explanations
        """
        try:
            # Get cached relationship data
            cache_key = f"collection_analysis_{user_id or 'global'}"
            if cache_key in self.relationship_cache:
                analysis = self.relationship_cache[cache_key]['analysis']
                
                # Find relationships for current document
                related_docs = []
                for relationship in analysis.get('relationships', []):
                    if relationship['doc1_id'] == current_doc_id:
                        related_docs.append({
                            'doc_id': relationship['doc2_id'],
                            'similarity_score': relationship['similarity_score'],
                            'relationship_type': relationship['relationship_type'],
                            'shared_terms': relationship.get('shared_terms', []),
                            'reason': f"Similar content (similarity: {relationship['similarity_score']:.2f})"
                        })
                    elif relationship['doc2_id'] == current_doc_id:
                        related_docs.append({
                            'doc_id': relationship['doc1_id'],
                            'similarity_score': relationship['similarity_score'],
                            'relationship_type': relationship['relationship_type'],
                            'shared_terms': relationship.get('shared_terms', []),
                            'reason': f"Similar content (similarity: {relationship['similarity_score']:.2f})"
                        })
                
                # Sort by similarity score
                related_docs.sort(key=lambda x: x['similarity_score'], reverse=True)
                
                return {
                    'success': True,
                    'current_document': current_doc_id,
                    'suggestions': related_docs[:10],  # Top 10 suggestions
                    'suggestion_count': len(related_docs)
                }
            else:
                return {'error': 'No relationship data available. Run collection analysis first.'}
                
        except Exception as e:
            self.logger.error(f"Document suggestions failed: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def create_knowledge_graph(self, user_id: str = None) -> Dict[str, Any]:
        """
        Create a knowledge graph representation of documents and relationships
        
        Args:
            user_id: User ID for scoped graph
            
        Returns:
            Knowledge graph data
        """
        try:
            if not HAS_NETWORKX:
                return {'error': 'NetworkX library required for knowledge graph creation'}
            
            # Get relationship analysis
            cache_key = f"collection_analysis_{user_id or 'global'}"
            if cache_key not in self.relationship_cache:
                # Run analysis if not cached
                analysis_result = self.analyze_document_collection(user_id)
                if not analysis_result.get('success'):
                    return analysis_result
            
            analysis = self.relationship_cache[cache_key]['analysis']
            
            # Create graph
            G = nx.Graph()
            
            # Add document nodes
            documents = set()
            for relationship in analysis.get('relationships', []):
                documents.add(relationship['doc1_id'])
                documents.add(relationship['doc2_id'])
            
            for doc_id in documents:
                G.add_node(doc_id, type='document')
            
            # Add relationship edges
            for relationship in analysis.get('relationships', []):
                G.add_edge(
                    relationship['doc1_id'],
                    relationship['doc2_id'],
                    weight=relationship['similarity_score'],
                    type=relationship['relationship_type']
                )
            
            # Add entity nodes and connections
            for entity_type, entities in analysis.get('shared_entities', {}).items():
                for entity_info in entities:
                    entity_id = f"{entity_type}_{entity_info['entity']}"
                    G.add_node(entity_id, type='entity', entity_type=entity_type, name=entity_info['entity'])
                    
                    # Connect entity to documents
                    for doc_id in entity_info['documents']:
                        if doc_id in documents:
                            G.add_edge(entity_id, doc_id, type='contains_entity')
            
            # Calculate graph metrics
            graph_metrics = {
                'nodes': G.number_of_nodes(),
                'edges': G.number_of_edges(),
                'density': nx.density(G),
                'connected_components': nx.number_connected_components(G),
                'average_clustering': nx.average_clustering(G) if G.number_of_nodes() > 0 else 0
            }
            
            # Find central documents
            if G.number_of_nodes() > 0:
                centrality = nx.degree_centrality(G)
                central_docs = sorted(
                    [(node, score) for node, score in centrality.items() if node in documents],
                    key=lambda x: x[1],
                    reverse=True
                )[:5]
            else:
                central_docs = []
            
            # Convert graph to serializable format
            graph_data = {
                'nodes': [
                    {
                        'id': node,
                        'type': G.nodes[node].get('type', 'unknown'),
                        'label': G.nodes[node].get('name', node),
                        'entity_type': G.nodes[node].get('entity_type', None)
                    }
                    for node in G.nodes()
                ],
                'edges': [
                    {
                        'source': edge[0],
                        'target': edge[1],
                        'weight': G.edges[edge].get('weight', 1.0),
                        'type': G.edges[edge].get('type', 'related')
                    }
                    for edge in G.edges()
                ]
            }
            
            return {
                'success': True,
                'graph_data': graph_data,
                'metrics': graph_metrics,
                'central_documents': central_docs,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Knowledge graph creation failed: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_search_recommendations(self, user_id: str = None) -> Dict[str, Any]:
        """
        Get search recommendations based on user history and document content
        
        Args:
            user_id: User ID for personalized recommendations
            
        Returns:
            Search recommendations
        """
        try:
            user_history = self._get_user_search_history(user_id)
            
            if not user_history:
                return {'message': 'No search history available for recommendations'}
            
            # Analyze search patterns
            common_terms = Counter()
            for search in user_history:
                query_terms = re.findall(r'\b[a-zA-Z]{3,}\b', search['query'].lower())
                common_terms.update(query_terms)
            
            # Generate recommendations based on patterns
            recommendations = []
            
            # Expand on common terms
            for term, count in common_terms.most_common(5):
                recommendations.append({
                    'type': 'expand_topic',
                    'suggestion': f"Learn more about {term}",
                    'query': f"detailed information about {term}",
                    'reason': f"You've searched for '{term}' {count} times"
                })
            
            # Related topic suggestions (this would be enhanced with actual document analysis)
            recommendations.append({
                'type': 'explore_related',
                'suggestion': 'Explore related documents',
                'query': 'find related documents',
                'reason': 'Discover connections between your interests'
            })
            
            return {
                'success': True,
                'recommendations': recommendations,
                'based_on_searches': len(user_history)
            }
            
        except Exception as e:
            self.logger.error(f"Search recommendations failed: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    # Helper methods
    
    def _enhance_search_results(self, base_results: List[Dict], query: str, user_id: str = None, context: Dict = None) -> List[Dict]:
        """Enhance search results with relationship information"""
        enhanced_results = []
        
        for result in base_results:
            enhanced_result = result.copy()
            
            # Add relationship information if available
            doc_id = result.get('id', result.get('document_id'))
            if doc_id:
                suggestions = self.get_document_suggestions(doc_id, user_id)
                if suggestions.get('success'):
                    enhanced_result['related_documents'] = suggestions['suggestions'][:3]  # Top 3
            
            # Add relevance scoring based on user preferences
            if user_id and user_id in self.user_preferences:
                relevance_boost = self._calculate_relevance_boost(result, self.user_preferences[user_id])
                enhanced_result['relevance_score'] = result.get('score', 0) + relevance_boost
            
            enhanced_results.append(enhanced_result)
        
        return enhanced_results
    
    def _get_all_documents_from_rag(self) -> List[Dict[str, Any]]:
        """
        Get all documents from the base RAG system
        This is a placeholder - implement based on your RAG system's API
        """
        # This would need to be implemented based on your specific RAG system
        # For now, return empty list
        return []
    
    def _add_to_search_history(self, query: str, results: List[Dict], user_id: str = None):
        """Add search to history"""
        search_entry = {
            'query': query,
            'timestamp': datetime.now().isoformat(),
            'result_count': len(results),
            'user_id': user_id
        }
        
        self.search_history.append(search_entry)
        
        # Keep only last 100 searches
        if len(self.search_history) > 100:
            self.search_history = self.search_history[-100:]
    
    def _get_user_search_history(self, user_id: str = None) -> List[Dict]:
        """Get search history for a user"""
        if user_id:
            return [search for search in self.search_history if search.get('user_id') == user_id]
        return self.search_history
    
    def _calculate_relevance_boost(self, result: Dict, preferences: Dict) -> float:
        """Calculate relevance boost based on user preferences"""
        # Simple implementation - could be much more sophisticated
        boost = 0.0
        
        content = result.get('content', '').lower()
        for preferred_term in preferences.get('preferred_topics', []):
            if preferred_term.lower() in content:
                boost += 0.1
        
        return boost
    
    def _generate_search_insights(self, results: List[Dict], query: str) -> List[str]:
        """Generate insights from search results"""
        insights = []
        
        if not results:
            insights.append("No results found. Try using different keywords or broader terms.")
            return insights
        
        # Analyze result diversity
        if len(results) > 1:
            insights.append(f"Found {len(results)} relevant documents")
        
        # Check for related documents
        related_count = sum(1 for result in results if result.get('related_documents'))
        if related_count > 0:
            insights.append(f"{related_count} results have related documents you might find interesting")
        
        return insights
    
    def _get_result_relationships(self, results: List[Dict]) -> Dict[str, Any]:
        """Get relationship information for search results"""
        # Placeholder for relationship data between search results
        return {
            'result_count': len(results),
            'has_relationships': any(result.get('related_documents') for result in results)
        }
    
    def _generate_collection_insights(self, analysis: Dict[str, Any]) -> List[str]:
        """Generate insights about the document collection"""
        insights = []
        
        if analysis.get('relationships'):
            strong_relationships = [r for r in analysis['relationships'] if r['similarity_score'] > 0.7]
            if strong_relationships:
                insights.append(f"Document collection has {len(strong_relationships)} strong content relationships")
        
        if analysis.get('document_clusters'):
            insights.append(f"Documents form {len(analysis['document_clusters'])} distinct topic clusters")
        
        if analysis.get('shared_entities'):
            entity_count = sum(len(entities) for entities in analysis['shared_entities'].values())
            insights.append(f"Found {entity_count} entities shared across multiple documents")
        
        return insights


def main():
    """Main function for testing"""
    rag = AdvancedRAGSystem()
    print("Advanced RAG System initialized")
    print(f"Has ChromaDB: {HAS_CHROMADB}")
    print(f"Has sklearn: {HAS_SKLEARN}")
    print(f"Has NetworkX: {HAS_NETWORKX}")


if __name__ == "__main__":
    main()
