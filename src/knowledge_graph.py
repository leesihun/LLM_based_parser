#!/usr/bin/env python3
"""
Knowledge Graph Module
Creates and manages knowledge graphs from document collections
with entity extraction, relationship mapping, and graph analysis
"""

import json
import logging
import re
from pathlib import Path
from typing import Dict, Any, List, Optional, Set, Tuple
from datetime import datetime
from collections import defaultdict, Counter
import hashlib

try:
    import networkx as nx
    HAS_NETWORKX = True
except ImportError:
    HAS_NETWORKX = False

try:
    import numpy as np
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    from sklearn.cluster import DBSCAN
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False


class EntityExtractor:
    """Advanced entity extraction from documents"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # Enhanced entity patterns
        self.entity_patterns = {
            'person': [
                r'\b[A-Z][a-z]+ [A-Z][a-z]+(?:\s+[A-Z][a-z]+)?\b',  # John Doe, John F. Kennedy
                r'\b(?:Dr|Mr|Ms|Mrs|Prof)\.?\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?\b',  # Dr. Smith
            ],
            'organization': [
                r'\b[A-Z][A-Za-z\s&]{2,40}(?:Inc|Corp|Ltd|LLC|Company|Organization|Institute|University|College)\b',
                r'\b(?:Apple|Google|Microsoft|Amazon|Facebook|Tesla|IBM|Oracle|Intel|Netflix)\b',  # Known companies
            ],
            'location': [
                r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+(?:City|State|County|Country|Street|Avenue|Road|Boulevard|Drive)\b',
                r'\b(?:New York|Los Angeles|Chicago|Houston|Phoenix|Philadelphia|San Antonio|San Diego|Dallas|San Jose)\b',  # Major cities
            ],
            'technology': [
                r'\b(?:Python|JavaScript|Java|C\+\+|React|Angular|Node\.js|Docker|Kubernetes|AWS|Azure|GCP)\b',
                r'\b(?:AI|ML|Machine Learning|Deep Learning|Neural Network|Algorithm|API|Database|Cloud)\b',
            ],
            'concept': [
                r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*(?:\s+(?:Theory|Method|Approach|Framework|Model|System))\b',
                r'\b(?:methodology|strategy|protocol|procedure|technique|principle|concept|paradigm)\b',
            ],
            'date': [
                r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b',
                r'\b\d{4}[/-]\d{1,2}[/-]\d{1,2}\b',
                r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}\b',
            ],
            'email': [
                r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            ],
            'url': [
                r'https?://[^\s<>"{\}|\\^`\[\]]+'
            ],
            'phone': [
                r'\b(?:\+?1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}\b'
            ],
            'currency': [
                r'\$\d{1,3}(?:,\d{3})*(?:\.\d{2})?',
                r'\b\d{1,3}(?:,\d{3})*(?:\.\d{2})?\s*(?:USD|EUR|GBP|JPY|dollars?|euros?)\b'
            ],
            'measurement': [
                r'\b\d+(?:\.\d+)?\s*(?:kg|g|lb|oz|m|cm|mm|ft|in|mile|km|liter|ml|gallon)\b',
                r'\b\d+(?:\.\d+)?\s*(?:percent|%|degree|°)\b'
            ]
        }
        
        # Entity relationship patterns
        self.relationship_patterns = {
            'works_at': r'(\b[A-Z][a-z]+ [A-Z][a-z]+)\s+(?:works at|employed by|at)\s+([A-Z][A-Za-z\s&]{2,40}(?:Inc|Corp|Ltd|LLC|Company))',
            'located_in': r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(?:in|at|located in)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            'developed_by': r'([A-Z][A-Za-z\s]+)\s+(?:developed by|created by|built by)\s+([A-Z][A-Za-z\s&]+)',
            'part_of': r'([A-Z][A-Za-z\s]+)\s+(?:is part of|belongs to|component of)\s+([A-Z][A-Za-z\s]+)',
            'uses': r'([A-Z][A-Za-z\s]+)\s+(?:uses|utilizes|implements|based on)\s+([A-Z][A-Za-z\s]+)',
        }
    
    def extract_entities(self, text: str, document_id: str = None) -> Dict[str, Any]:
        """
        Extract entities from text
        
        Args:
            text: Text to extract entities from
            document_id: Document identifier
            
        Returns:
            Dictionary of extracted entities by type
        """
        try:
            extracted = {
                'document_id': document_id,
                'entities': defaultdict(list),
                'relationships': [],
                'entity_positions': defaultdict(list),
                'timestamp': datetime.now().isoformat()
            }
            
            # Extract entities by type
            for entity_type, patterns in self.entity_patterns.items():
                for pattern in patterns:
                    matches = list(re.finditer(pattern, text, re.IGNORECASE))
                    for match in matches:
                        entity = match.group().strip()
                        if len(entity) > 2 and self._is_valid_entity(entity, entity_type):
                            entity_info = {
                                'text': entity,
                                'start': match.start(),
                                'end': match.end(),
                                'confidence': self._calculate_entity_confidence(entity, entity_type, text),
                                'context': self._get_entity_context(text, match.start(), match.end())
                            }
                            extracted['entities'][entity_type].append(entity_info)
                            extracted['entity_positions'][entity_type].append((match.start(), match.end()))
            
            # Extract relationships
            extracted['relationships'] = self._extract_relationships(text)
            
            # Remove duplicates and sort by confidence
            for entity_type in extracted['entities']:
                extracted['entities'][entity_type] = self._deduplicate_entities(extracted['entities'][entity_type])
            
            return dict(extracted)
            
        except Exception as e:
            self.logger.error(f"Entity extraction failed: {str(e)}")
            return {'error': str(e), 'document_id': document_id}
    
    def _is_valid_entity(self, entity: str, entity_type: str) -> bool:
        """Validate extracted entity"""
        # Remove very short entities
        if len(entity) < 3:
            return False
        
        # Remove common false positives
        false_positives = {
            'person': ['The User', 'Mr User', 'Ms User', 'New User'],
            'organization': ['The Company', 'Your Company', 'Our Company'],
            'location': ['The City', 'Your City', 'This City'],
        }
        
        if entity in false_positives.get(entity_type, []):
            return False
        
        # Additional validation based on entity type
        if entity_type == 'person':
            # Person names should have at least 2 words
            parts = entity.split()
            if len(parts) < 2:
                return False
            # Should not be all uppercase (likely an acronym)
            if entity.isupper():
                return False
        
        elif entity_type == 'email':
            # Basic email validation
            return '@' in entity and '.' in entity
        
        elif entity_type == 'url':
            # Basic URL validation
            return entity.startswith(('http://', 'https://'))
        
        return True
    
    def _calculate_entity_confidence(self, entity: str, entity_type: str, full_text: str) -> float:
        """Calculate confidence score for extracted entity"""
        confidence = 0.5  # Base confidence
        
        # Boost confidence based on entity characteristics
        if entity_type == 'person':
            # Names with titles get higher confidence
            if any(title in entity for title in ['Dr.', 'Mr.', 'Ms.', 'Mrs.', 'Prof.']):
                confidence += 0.2
            # Proper capitalization
            if all(part[0].isupper() and part[1:].islower() for part in entity.split() if len(part) > 1):
                confidence += 0.1
        
        elif entity_type == 'organization':
            # Companies with legal suffixes get higher confidence
            if any(suffix in entity for suffix in ['Inc', 'Corp', 'Ltd', 'LLC', 'Company']):
                confidence += 0.2
        
        elif entity_type == 'email':
            # Valid email format
            if re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', entity):
                confidence += 0.3
        
        # Frequency boost - entities mentioned multiple times get higher confidence
        frequency = full_text.lower().count(entity.lower())
        confidence += min(0.2, frequency * 0.05)
        
        return min(1.0, confidence)
    
    def _get_entity_context(self, text: str, start: int, end: int, context_size: int = 50) -> str:
        """Get context around an entity"""
        context_start = max(0, start - context_size)
        context_end = min(len(text), end + context_size)
        return text[context_start:context_end].strip()
    
    def _extract_relationships(self, text: str) -> List[Dict[str, Any]]:
        """Extract relationships between entities"""
        relationships = []
        
        for rel_type, pattern in self.relationship_patterns.items():
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                if len(match.groups()) >= 2:
                    relationships.append({
                        'type': rel_type,
                        'source': match.group(1).strip(),
                        'target': match.group(2).strip(),
                        'context': self._get_entity_context(text, match.start(), match.end()),
                        'confidence': 0.7  # Default confidence for pattern-based relationships
                    })
        
        return relationships
    
    def _deduplicate_entities(self, entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate entities and keep highest confidence ones"""
        seen = {}
        for entity in entities:
            text = entity['text'].lower()
            if text not in seen or entity['confidence'] > seen[text]['confidence']:
                seen[text] = entity
        
        # Sort by confidence
        return sorted(seen.values(), key=lambda x: x['confidence'], reverse=True)


class KnowledgeGraph:
    """Knowledge graph construction and analysis"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        if not HAS_NETWORKX:
            raise ImportError("NetworkX is required for knowledge graph functionality")
        
        # Initialize graph
        self.graph = nx.MultiDiGraph()  # Directed graph with multiple edges
        self.entity_extractor = EntityExtractor(config)
        
        # Graph metadata
        self.metadata = {
            'created': datetime.now().isoformat(),
            'documents_processed': 0,
            'total_entities': 0,
            'total_relationships': 0
        }
        
        # Entity type colors for visualization
        self.entity_colors = {
            'person': '#FF6B6B',
            'organization': '#4ECDC4',
            'location': '#45B7D1',
            'technology': '#96CEB4',
            'concept': '#FFEAA7',
            'date': '#DDA0DD',
            'email': '#98D8C8',
            'url': '#F7DC6F',
            'phone': '#BB8FCE',
            'currency': '#85C1E9',
            'measurement': '#F8C471'
        }
    
    def add_document(self, document_id: str, content: str, metadata: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Add a document to the knowledge graph
        
        Args:
            document_id: Unique document identifier
            content: Document content
            metadata: Optional document metadata
            
        Returns:
            Processing results
        """
        try:
            # Extract entities from document
            extraction_result = self.entity_extractor.extract_entities(content, document_id)
            
            if 'error' in extraction_result:
                return extraction_result
            
            # Add document node
            self.graph.add_node(
                document_id,
                type='document',
                content_length=len(content),
                entity_count=sum(len(entities) for entities in extraction_result['entities'].values()),
                metadata=metadata or {},
                processed_date=datetime.now().isoformat()
            )
            
            entities_added = 0
            relationships_added = 0
            
            # Add entity nodes and relationships
            for entity_type, entities in extraction_result['entities'].items():
                for entity in entities:
                    entity_id = self._create_entity_id(entity['text'], entity_type)
                    
                    # Add entity node if it doesn't exist
                    if entity_id not in self.graph:
                        self.graph.add_node(
                            entity_id,
                            type='entity',
                            entity_type=entity_type,
                            text=entity['text'],
                            first_seen=datetime.now().isoformat(),
                            documents=[document_id],
                            total_mentions=1
                        )
                        entities_added += 1
                    else:
                        # Update existing entity
                        if document_id not in self.graph.nodes[entity_id]['documents']:
                            self.graph.nodes[entity_id]['documents'].append(document_id)
                        self.graph.nodes[entity_id]['total_mentions'] += 1
                    
                    # Add relationship between document and entity
                    self.graph.add_edge(
                        document_id,
                        entity_id,
                        type='contains',
                        confidence=entity['confidence'],
                        context=entity['context']
                    )
                    relationships_added += 1
            
            # Add extracted relationships
            for relationship in extraction_result.get('relationships', []):
                source_id = self._find_entity_by_text(relationship['source'])
                target_id = self._find_entity_by_text(relationship['target'])
                
                if source_id and target_id:
                    self.graph.add_edge(
                        source_id,
                        target_id,
                        type=relationship['type'],
                        confidence=relationship['confidence'],
                        context=relationship['context'],
                        source_document=document_id
                    )
                    relationships_added += 1
            
            # Update metadata
            self.metadata['documents_processed'] += 1
            self.metadata['total_entities'] = len([n for n in self.graph.nodes() if self.graph.nodes[n]['type'] == 'entity'])
            self.metadata['total_relationships'] = self.graph.number_of_edges()
            
            return {
                'success': True,
                'document_id': document_id,
                'entities_added': entities_added,
                'relationships_added': relationships_added,
                'extraction_result': extraction_result
            }
            
        except Exception as e:
            self.logger.error(f"Error adding document to knowledge graph: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def get_document_relationships(self, document_id: str) -> Dict[str, Any]:
        """
        Get relationships for a specific document
        
        Args:
            document_id: Document identifier
            
        Returns:
            Document relationships and connected entities
        """
        try:
            if document_id not in self.graph:
                return {'error': 'Document not found in knowledge graph'}
            
            # Get direct connections (entities in the document)
            direct_entities = []
            for neighbor in self.graph.neighbors(document_id):
                if self.graph.nodes[neighbor]['type'] == 'entity':
                    edge_data = self.graph[document_id][neighbor]
                    if edge_data:
                        edge_info = list(edge_data.values())[0]  # Get first edge data
                        direct_entities.append({
                            'entity_id': neighbor,
                            'entity_type': self.graph.nodes[neighbor]['entity_type'],
                            'text': self.graph.nodes[neighbor]['text'],
                            'confidence': edge_info.get('confidence', 0),
                            'context': edge_info.get('context', '')
                        })
            
            # Find related documents through shared entities
            related_documents = defaultdict(list)
            for entity in direct_entities:
                entity_id = entity['entity_id']
                for doc_neighbor in self.graph.neighbors(entity_id):
                    if (self.graph.nodes[doc_neighbor]['type'] == 'document' and 
                        doc_neighbor != document_id):
                        related_documents[doc_neighbor].append(entity)
            
            # Calculate relationship strength
            document_relationships = []
            for related_doc, shared_entities in related_documents.items():
                strength = len(shared_entities) / max(len(direct_entities), 1)
                document_relationships.append({
                    'document_id': related_doc,
                    'relationship_strength': strength,
                    'shared_entities': len(shared_entities),
                    'shared_entity_details': shared_entities[:5]  # Top 5
                })
            
            # Sort by relationship strength
            document_relationships.sort(key=lambda x: x['relationship_strength'], reverse=True)
            
            return {
                'success': True,
                'document_id': document_id,
                'direct_entities': direct_entities,
                'related_documents': document_relationships,
                'entity_count': len(direct_entities)
            }
            
        except Exception as e:
            self.logger.error(f"Error getting document relationships: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def search_entities(self, query: str, entity_types: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Search for entities in the knowledge graph
        
        Args:
            query: Search query
            entity_types: Optional filter by entity types
            
        Returns:
            Search results with entity information
        """
        try:
            results = []
            query_lower = query.lower()
            
            for node_id, node_data in self.graph.nodes(data=True):
                if node_data['type'] == 'entity':
                    # Filter by entity type if specified
                    if entity_types and node_data['entity_type'] not in entity_types:
                        continue
                    
                    entity_text = node_data['text'].lower()
                    
                    # Calculate relevance score
                    relevance = 0
                    if query_lower in entity_text:
                        relevance = 1.0
                    elif any(word in entity_text for word in query_lower.split()):
                        relevance = 0.5
                    
                    if relevance > 0:
                        # Get connected documents
                        connected_docs = []
                        for neighbor in self.graph.neighbors(node_id):
                            if self.graph.nodes[neighbor]['type'] == 'document':
                                connected_docs.append(neighbor)
                        
                        results.append({
                            'entity_id': node_id,
                            'text': node_data['text'],
                            'entity_type': node_data['entity_type'],
                            'relevance': relevance,
                            'total_mentions': node_data.get('total_mentions', 1),
                            'connected_documents': connected_docs,
                            'document_count': len(connected_docs)
                        })
            
            # Sort by relevance and mention count
            results.sort(key=lambda x: (x['relevance'], x['total_mentions']), reverse=True)
            
            return {
                'success': True,
                'query': query,
                'results': results[:20],  # Top 20 results
                'total_found': len(results)
            }
            
        except Exception as e:
            self.logger.error(f"Error searching entities: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def get_graph_analytics(self) -> Dict[str, Any]:
        """
        Get analytics and metrics for the knowledge graph
        
        Returns:
            Graph analytics and statistics
        """
        try:
            analytics = {
                'basic_metrics': {
                    'total_nodes': self.graph.number_of_nodes(),
                    'total_edges': self.graph.number_of_edges(),
                    'density': nx.density(self.graph),
                    'is_connected': nx.is_weakly_connected(self.graph)
                },
                'node_types': {},
                'entity_types': {},
                'top_entities': [],
                'most_connected_documents': [],
                'relationship_types': {}
            }
            
            # Count node types
            for node, data in self.graph.nodes(data=True):
                node_type = data.get('type', 'unknown')
                analytics['node_types'][node_type] = analytics['node_types'].get(node_type, 0) + 1
                
                if node_type == 'entity':
                    entity_type = data.get('entity_type', 'unknown')
                    analytics['entity_types'][entity_type] = analytics['entity_types'].get(entity_type, 0) + 1
            
            # Find top entities by mention count
            entities_by_mentions = []
            for node, data in self.graph.nodes(data=True):
                if data.get('type') == 'entity':
                    mentions = data.get('total_mentions', 1)
                    entities_by_mentions.append({
                        'entity_id': node,
                        'text': data.get('text', ''),
                        'entity_type': data.get('entity_type', ''),
                        'mentions': mentions,
                        'document_count': len(data.get('documents', []))
                    })
            
            entities_by_mentions.sort(key=lambda x: x['mentions'], reverse=True)
            analytics['top_entities'] = entities_by_mentions[:10]
            
            # Find most connected documents
            docs_by_connections = []
            for node, data in self.graph.nodes(data=True):
                if data.get('type') == 'document':
                    degree = self.graph.degree(node)
                    docs_by_connections.append({
                        'document_id': node,
                        'connections': degree,
                        'entity_count': data.get('entity_count', 0)
                    })
            
            docs_by_connections.sort(key=lambda x: x['connections'], reverse=True)
            analytics['most_connected_documents'] = docs_by_connections[:10]
            
            # Count relationship types
            for source, target, data in self.graph.edges(data=True):
                rel_type = data.get('type', 'unknown')
                analytics['relationship_types'][rel_type] = analytics['relationship_types'].get(rel_type, 0) + 1
            
            # Calculate centrality measures if graph is not too large
            if self.graph.number_of_nodes() < 1000:
                try:
                    centrality = nx.degree_centrality(self.graph)
                    top_central = sorted(centrality.items(), key=lambda x: x[1], reverse=True)[:5]
                    analytics['most_central_nodes'] = [
                        {
                            'node_id': node_id,
                            'centrality': score,
                            'type': self.graph.nodes[node_id].get('type', 'unknown')
                        }
                        for node_id, score in top_central
                    ]
                except Exception as e:
                    self.logger.warning(f"Could not calculate centrality: {str(e)}")
            
            analytics['metadata'] = self.metadata
            return analytics
            
        except Exception as e:
            self.logger.error(f"Error getting graph analytics: {str(e)}")
            return {'error': str(e)}
    
    def export_graph(self, format_type: str = 'json') -> Dict[str, Any]:
        """
        Export the knowledge graph in various formats
        
        Args:
            format_type: Export format ('json', 'gexf', 'graphml')
            
        Returns:
            Exported graph data or file path
        """
        try:
            if format_type == 'json':
                # Convert to JSON serializable format
                nodes = []
                for node_id, data in self.graph.nodes(data=True):
                    node_data = {
                        'id': node_id,
                        'type': data.get('type', 'unknown'),
                        'label': data.get('text', node_id)
                    }
                    
                    # Add type-specific data
                    if data.get('type') == 'entity':
                        node_data.update({
                            'entity_type': data.get('entity_type'),
                            'mentions': data.get('total_mentions', 1),
                            'documents': data.get('documents', []),
                            'color': self.entity_colors.get(data.get('entity_type'), '#CCCCCC')
                        })
                    elif data.get('type') == 'document':
                        node_data.update({
                            'content_length': data.get('content_length', 0),
                            'entity_count': data.get('entity_count', 0),
                            'color': '#E0E0E0'
                        })
                    
                    nodes.append(node_data)
                
                edges = []
                for source, target, data in self.graph.edges(data=True):
                    edges.append({
                        'source': source,
                        'target': target,
                        'type': data.get('type', 'related'),
                        'confidence': data.get('confidence', 0.5),
                        'weight': data.get('confidence', 0.5)
                    })
                
                return {
                    'success': True,
                    'format': 'json',
                    'data': {
                        'nodes': nodes,
                        'edges': edges,
                        'metadata': self.metadata
                    }
                }
            
            else:
                return {'success': False, 'error': f'Export format "{format_type}" not supported'}
                
        except Exception as e:
            self.logger.error(f"Error exporting graph: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def find_shortest_path(self, source_id: str, target_id: str) -> Dict[str, Any]:
        """
        Find shortest path between two nodes
        
        Args:
            source_id: Source node ID
            target_id: Target node ID
            
        Returns:
            Shortest path information
        """
        try:
            if source_id not in self.graph or target_id not in self.graph:
                return {'error': 'One or both nodes not found in graph'}
            
            try:
                # Convert to undirected for path finding
                undirected = self.graph.to_undirected()
                path = nx.shortest_path(undirected, source_id, target_id)
                path_length = len(path) - 1
                
                # Get path details
                path_details = []
                for i in range(len(path) - 1):
                    current = path[i]
                    next_node = path[i + 1]
                    
                    # Get edge data
                    edge_data = {}
                    if self.graph.has_edge(current, next_node):
                        edge_data = list(self.graph[current][next_node].values())[0]
                    elif self.graph.has_edge(next_node, current):
                        edge_data = list(self.graph[next_node][current].values())[0]
                    
                    path_details.append({
                        'from': current,
                        'to': next_node,
                        'relationship': edge_data.get('type', 'connected'),
                        'from_type': self.graph.nodes[current].get('type', 'unknown'),
                        'to_type': self.graph.nodes[next_node].get('type', 'unknown')
                    })
                
                return {
                    'success': True,
                    'path': path,
                    'path_length': path_length,
                    'path_details': path_details
                }
                
            except nx.NetworkXNoPath:
                return {'error': 'No path found between the specified nodes'}
                
        except Exception as e:
            self.logger.error(f"Error finding shortest path: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    # Helper methods
    
    def _create_entity_id(self, text: str, entity_type: str) -> str:
        """Create unique entity ID"""
        # Normalize text for consistent IDs
        normalized = re.sub(r'\s+', '_', text.lower().strip())
        return f"{entity_type}_{normalized}"
    
    def _find_entity_by_text(self, text: str) -> Optional[str]:
        """Find entity ID by text"""
        text_lower = text.lower()
        for node_id, data in self.graph.nodes(data=True):
            if (data.get('type') == 'entity' and 
                data.get('text', '').lower() == text_lower):
                return node_id
        return None
    
    def save_graph(self, file_path: str) -> Dict[str, Any]:
        """Save knowledge graph to file"""
        try:
            # Export as JSON and save
            export_result = self.export_graph('json')
            if export_result.get('success'):
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(export_result['data'], f, indent=2, ensure_ascii=False)
                
                return {
                    'success': True,
                    'file_path': file_path,
                    'nodes': self.graph.number_of_nodes(),
                    'edges': self.graph.number_of_edges()
                }
            else:
                return export_result
                
        except Exception as e:
            self.logger.error(f"Error saving graph: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def load_graph(self, file_path: str) -> Dict[str, Any]:
        """Load knowledge graph from file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Clear existing graph
            self.graph.clear()
            
            # Load nodes
            for node in data['nodes']:
                node_data = node.copy()
                node_id = node_data.pop('id')
                self.graph.add_node(node_id, **node_data)
            
            # Load edges
            for edge in data['edges']:
                self.graph.add_edge(
                    edge['source'],
                    edge['target'],
                    **{k: v for k, v in edge.items() if k not in ['source', 'target']}
                )
            
            # Update metadata
            self.metadata = data.get('metadata', self.metadata)
            
            return {
                'success': True,
                'file_path': file_path,
                'nodes_loaded': self.graph.number_of_nodes(),
                'edges_loaded': self.graph.number_of_edges()
            }
            
        except Exception as e:
            self.logger.error(f"Error loading graph: {str(e)}")
            return {'success': False, 'error': str(e)}


def main():
    """Main function for testing"""
    if not HAS_NETWORKX:
        print("NetworkX not available - knowledge graph functionality disabled")
        return
    
    kg = KnowledgeGraph()
    print("Knowledge Graph initialized")
    print(f"Supported entity types: {list(kg.entity_extractor.entity_patterns.keys())}")
    print(f"Graph empty: {kg.graph.number_of_nodes() == 0}")


if __name__ == "__main__":
    main()