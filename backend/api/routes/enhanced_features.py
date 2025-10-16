"""
Enhanced Features API Endpoints
Provides REST API endpoints for advanced file processing, RAG features, and knowledge graph functionality
"""

from flask import request, jsonify
from functools import wraps
from typing import Dict, Any, Optional, Tuple
import logging
import json
import os
from pathlib import Path
import tempfile
import base64

logger = logging.getLogger(__name__)


def create_enhanced_features_endpoints(app, user_manager, enhanced_processor=None, advanced_rag=None, knowledge_graph=None):
    """
    Create enhanced features endpoints
    
    Args:
        app: Flask application instance
        user_manager: UserManager instance
        enhanced_processor: EnhancedFileProcessor instance
        advanced_rag: AdvancedRAGSystem instance
        knowledge_graph: KnowledgeGraph instance
    """
    
    def require_auth(f):
        """Decorator to require authentication for endpoints"""
        @wraps(f)
        def decorated_function(*args, **kwargs):
            auth_header = request.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                return jsonify({'error': 'Authentication required'}), 401
            
            token = auth_header.split(' ')[1]
            session_data = user_manager.validate_session(token)
            if not session_data:
                return jsonify({'error': 'Invalid or expired token'}), 401
            
            # Add user info to request context
            request.user_data = session_data
            return f(*args, **kwargs)
        
        return decorated_function
    
    # ========== ENHANCED FILE PROCESSING ENDPOINTS ==========
    
    @app.route('/api/files/analyze', methods=['POST'])
    @require_auth
    def analyze_file() -> Tuple[Dict[str, Any], int]:
        """
        Analyze uploaded file with enhanced processing
        
        Headers:
            Authorization: Bearer <session_token>
            Content-Type: application/json
            
        Request Body:
            file_id (str): File ID from previous upload
            analysis_types (list, optional): Types of analysis to perform
            
        Returns:
            200: Analysis results
            400: Invalid request
            404: File not found
            500: Processing error
        """
        try:
            if not enhanced_processor:
                return jsonify({'error': 'Enhanced file processing not available'}), 503
            
            data = request.get_json()
            if not data or 'file_id' not in data:
                return jsonify({'error': 'file_id is required'}), 400
            
            file_id = data['file_id']
            user_id = request.user_data['user_id']
            analysis_types = data.get('analysis_types', ['all'])
            
            # Get file information from the existing file handler
            # This would need integration with your existing file system
            file_path = f"uploads/{user_id}/{file_id}"
            file_type = Path(file_id).suffix.lower()
            
            if not Path(file_path).exists():
                return jsonify({'error': 'File not found'}), 404
            
            # Perform enhanced analysis
            analysis_result = enhanced_processor.analyze_file(file_path, file_type, user_id)
            
            if not analysis_result.get('success'):
                return jsonify({'error': analysis_result.get('error', 'Analysis failed')}), 500
            
            return jsonify({
                'success': True,
                'file_id': file_id,
                'analysis': analysis_result['analysis'],
                'file_info': {
                    'type': analysis_result['file_type'],
                    'category': analysis_result['category'],
                    'size': analysis_result['size']
                }
            }), 200
            
        except Exception as e:
            logger.error(f"File analysis error: {str(e)}")
            return jsonify({'error': 'Internal server error'}), 500
    
    @app.route('/api/files/code-analysis', methods=['POST'])
    @require_auth
    def analyze_code_file() -> Tuple[Dict[str, Any], int]:
        """
        Specialized code file analysis
        
        Headers:
            Authorization: Bearer <session_token>
            Content-Type: application/json
            
        Request Body:
            file_id (str): File ID of code file
            include_security (bool, optional): Include security analysis
            include_metrics (bool, optional): Include complexity metrics
            
        Returns:
            200: Code analysis results
            400: Invalid request or not a code file
            404: File not found
            500: Processing error
        """
        try:
            if not enhanced_processor:
                return jsonify({'error': 'Enhanced file processing not available'}), 503
            
            data = request.get_json()
            if not data or 'file_id' not in data:
                return jsonify({'error': 'file_id is required'}), 400
            
            file_id = data['file_id']
            user_id = request.user_data['user_id']
            include_security = data.get('include_security', True)
            include_metrics = data.get('include_metrics', True)
            
            file_path = f"uploads/{user_id}/{file_id}"
            file_type = Path(file_id).suffix.lower()
            
            # Check if it's a code file
            code_extensions = ['.py', '.js', '.ts', '.java', '.cpp', '.c', '.cs', '.php', '.rb', '.go']
            if file_type not in code_extensions:
                return jsonify({'error': 'File is not a recognized code file'}), 400
            
            if not Path(file_path).exists():
                return jsonify({'error': 'File not found'}), 404
            
            # Perform code-specific analysis
            analysis_result = enhanced_processor.analyze_file(file_path, file_type, user_id)
            
            if not analysis_result.get('success'):
                return jsonify({'error': analysis_result.get('error', 'Analysis failed')}), 500
            
            code_analysis = analysis_result['analysis']
            
            # Filter results based on request parameters
            if not include_security:
                code_analysis.pop('security_analysis', None)
            if not include_metrics:
                code_analysis.pop('complexity', None)
            
            return jsonify({
                'success': True,
                'file_id': file_id,
                'language': file_type[1:],  # Remove the dot
                'analysis': code_analysis,
                'recommendations': generate_code_recommendations(code_analysis)
            }), 200
            
        except Exception as e:
            logger.error(f"Code analysis error: {str(e)}")
            return jsonify({'error': 'Internal server error'}), 500
    
    @app.route('/api/files/image-ocr', methods=['POST'])
    @require_auth
    def perform_ocr_analysis() -> Tuple[Dict[str, Any], int]:
        """
        Perform OCR analysis on image files
        
        Headers:
            Authorization: Bearer <session_token>
            Content-Type: application/json or multipart/form-data
            
        Request Body (JSON):
            file_id (str): File ID of image
            enhance_image (bool, optional): Apply image enhancement
            
        Request Body (multipart):
            image: Image file
            enhance_image (bool, optional): Apply image enhancement
            
        Returns:
            200: OCR results with extracted text and data
            400: Invalid request or not an image file
            404: File not found
            500: Processing error
        """
        try:
            if not enhanced_processor:
                return jsonify({'error': 'Enhanced file processing not available'}), 503
            
            user_id = request.user_data['user_id']
            file_path = None
            temp_file = None
            
            # Handle different input types
            if request.content_type and 'multipart/form-data' in request.content_type:
                # Direct file upload
                if 'image' not in request.files:
                    return jsonify({'error': 'No image file provided'}), 400
                
                file = request.files['image']
                if file.filename == '':
                    return jsonify({'error': 'No file selected'}), 400
                
                # Save to temporary file
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix)
                file.save(temp_file.name)
                file_path = temp_file.name
                file_type = Path(file.filename).suffix.lower()
                
            else:
                # JSON with file_id
                data = request.get_json()
                if not data or 'file_id' not in data:
                    return jsonify({'error': 'file_id or image file is required'}), 400
                
                file_id = data['file_id']
                file_path = f"uploads/{user_id}/{file_id}"
                file_type = Path(file_id).suffix.lower()
                
                if not Path(file_path).exists():
                    return jsonify({'error': 'File not found'}), 404
            
            # Check if it's an image file
            image_extensions = ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.tif', '.webp']
            if file_type not in image_extensions:
                return jsonify({'error': 'File is not a recognized image format'}), 400
            
            # Perform OCR analysis
            analysis_result = enhanced_processor.analyze_file(file_path, file_type, user_id)
            
            # Clean up temporary file
            if temp_file:
                os.unlink(temp_file.name)
            
            if not analysis_result.get('success'):
                return jsonify({'error': analysis_result.get('error', 'OCR analysis failed')}), 500
            
            image_analysis = analysis_result['analysis']
            
            return jsonify({
                'success': True,
                'extracted_text': image_analysis.get('extracted_text', ''),
                'text_confidence': image_analysis.get('text_confidence', 0),
                'image_info': {
                    'format': image_analysis.get('format'),
                    'size': image_analysis.get('size'),
                    'mode': image_analysis.get('mode')
                },
                'data_extraction': image_analysis.get('data_extraction', {}),
                'analysis_type': image_analysis.get('type')
            }), 200
            
        except Exception as e:
            logger.error(f"OCR analysis error: {str(e)}")
            return jsonify({'error': 'Internal server error'}), 500
    
    # ========== ADVANCED RAG ENDPOINTS ==========
    
    @app.route('/api/rag/enhanced-search', methods=['POST'])
    @require_auth
    def enhanced_rag_search() -> Tuple[Dict[str, Any], int]:
        """
        Enhanced RAG search with relationship analysis
        
        Headers:
            Authorization: Bearer <session_token>
            Content-Type: application/json
            
        Request Body:
            query (str): Search query
            include_relationships (bool, optional): Include document relationships
            max_results (int, optional): Maximum results to return
            
        Returns:
            200: Enhanced search results with relationships
            400: Invalid request
            500: Search error
        """
        try:
            if not advanced_rag:
                return jsonify({'error': 'Advanced RAG system not available'}), 503
            
            data = request.get_json()
            if not data or 'query' not in data:
                return jsonify({'error': 'query is required'}), 400
            
            query = data['query']
            user_id = request.user_data['user_id']
            include_relationships = data.get('include_relationships', True)
            max_results = data.get('max_results', 10)
            
            # Perform enhanced search
            search_result = advanced_rag.enhanced_search(
                query=query,
                user_id=user_id,
                context={'max_results': max_results}
            )
            
            if not search_result.get('success'):
                return jsonify({'error': search_result.get('error', 'Search failed')}), 500
            
            response = {
                'success': True,
                'query': query,
                'results': search_result['results'][:max_results],
                'insights': search_result.get('insights', []),
                'total_results': len(search_result['results'])
            }
            
            if include_relationships:
                response['relationship_data'] = search_result.get('relationship_data', {})
            
            return jsonify(response), 200
            
        except Exception as e:
            logger.error(f"Enhanced search error: {str(e)}")
            return jsonify({'error': 'Internal server error'}), 500
    
    @app.route('/api/rag/collection-analysis', methods=['POST'])
    @require_auth
    def analyze_document_collection() -> Tuple[Dict[str, Any], int]:
        """
        Analyze document collection for relationships and insights
        
        Headers:
            Authorization: Bearer <session_token>
            Content-Type: application/json
            
        Request Body:
            scope (str, optional): Analysis scope ('user' or 'global')
            force_refresh (bool, optional): Force new analysis
            
        Returns:
            200: Collection analysis results
            500: Analysis error
        """
        try:
            if not advanced_rag:
                return jsonify({'error': 'Advanced RAG system not available'}), 503
            
            data = request.get_json() or {}
            user_id = request.user_data['user_id']
            scope = data.get('scope', 'user')
            force_refresh = data.get('force_refresh', False)
            
            # Use user_id for user scope, None for global scope
            analysis_user_id = user_id if scope == 'user' else None
            
            # Perform collection analysis
            analysis_result = advanced_rag.analyze_document_collection(analysis_user_id)
            
            if not analysis_result.get('success'):
                return jsonify({'error': analysis_result.get('error', 'Analysis failed')}), 500
            
            return jsonify({
                'success': True,
                'scope': scope,
                'analysis': analysis_result['analysis'],
                'collection_insights': analysis_result.get('collection_insights', []),
                'document_count': analysis_result.get('document_count', 0),
                'timestamp': analysis_result.get('timestamp')
            }), 200
            
        except Exception as e:
            logger.error(f"Collection analysis error: {str(e)}")
            return jsonify({'error': 'Internal server error'}), 500
    
    @app.route('/api/rag/document-suggestions/<document_id>', methods=['GET'])
    @require_auth
    def get_document_suggestions(document_id: str) -> Tuple[Dict[str, Any], int]:
        """
        Get related document suggestions
        
        Headers:
            Authorization: Bearer <session_token>
            
        URL Parameters:
            document_id: Document ID to find suggestions for
            
        Query Parameters:
            max_suggestions (int, optional): Maximum suggestions to return
            
        Returns:
            200: Document suggestions with relationship explanations
            404: Document not found
            500: Error getting suggestions
        """
        try:
            if not advanced_rag:
                return jsonify({'error': 'Advanced RAG system not available'}), 503
            
            user_id = request.user_data['user_id']
            max_suggestions = request.args.get('max_suggestions', 10, type=int)
            
            # Get suggestions
            suggestions_result = advanced_rag.get_document_suggestions(document_id, user_id)
            
            if not suggestions_result.get('success'):
                error = suggestions_result.get('error', 'Could not get suggestions')
                if 'not found' in error.lower():
                    return jsonify({'error': error}), 404
                else:
                    return jsonify({'error': error}), 500
            
            suggestions = suggestions_result.get('suggestions', [])[:max_suggestions]
            
            return jsonify({
                'success': True,
                'document_id': document_id,
                'suggestions': suggestions,
                'suggestion_count': len(suggestions),
                'total_available': suggestions_result.get('suggestion_count', 0)
            }), 200
            
        except Exception as e:
            logger.error(f"Document suggestions error: {str(e)}")
            return jsonify({'error': 'Internal server error'}), 500
    
    @app.route('/api/rag/search-recommendations', methods=['GET'])
    @require_auth
    def get_search_recommendations() -> Tuple[Dict[str, Any], int]:
        """
        Get personalized search recommendations
        
        Headers:
            Authorization: Bearer <session_token>
            
        Query Parameters:
            limit (int, optional): Maximum recommendations to return
            
        Returns:
            200: Search recommendations based on history and content
            500: Error getting recommendations
        """
        try:
            if not advanced_rag:
                return jsonify({'error': 'Advanced RAG system not available'}), 503
            
            user_id = request.user_data['user_id']
            limit = request.args.get('limit', 5, type=int)
            
            # Get recommendations
            recommendations_result = advanced_rag.get_search_recommendations(user_id)
            
            if not recommendations_result.get('success'):
                return jsonify({'error': recommendations_result.get('error', 'Could not get recommendations')}), 500
            
            recommendations = recommendations_result.get('recommendations', [])[:limit]
            
            return jsonify({
                'success': True,
                'recommendations': recommendations,
                'based_on_searches': recommendations_result.get('based_on_searches', 0)
            }), 200
            
        except Exception as e:
            logger.error(f"Search recommendations error: {str(e)}")
            return jsonify({'error': 'Internal server error'}), 500
    
    # ========== KNOWLEDGE GRAPH ENDPOINTS ==========
    
    @app.route('/api/knowledge-graph/add-document', methods=['POST'])
    @require_auth
    def add_document_to_graph() -> Tuple[Dict[str, Any], int]:
        """
        Add document to knowledge graph
        
        Headers:
            Authorization: Bearer <session_token>
            Content-Type: application/json
            
        Request Body:
            document_id (str): Document identifier
            content (str): Document content
            metadata (dict, optional): Document metadata
            
        Returns:
            200: Document added successfully
            400: Invalid request
            500: Processing error
        """
        try:
            if not knowledge_graph:
                return jsonify({'error': 'Knowledge graph not available'}), 503
            
            data = request.get_json()
            if not data or 'document_id' not in data or 'content' not in data:
                return jsonify({'error': 'document_id and content are required'}), 400
            
            document_id = data['document_id']
            content = data['content']
            metadata = data.get('metadata', {})
            
            # Add user context to metadata
            metadata['user_id'] = request.user_data['user_id']
            
            # Add document to graph
            result = knowledge_graph.add_document(document_id, content, metadata)
            
            if not result.get('success'):
                return jsonify({'error': result.get('error', 'Failed to add document')}), 500
            
            return jsonify({
                'success': True,
                'document_id': document_id,
                'entities_added': result.get('entities_added', 0),
                'relationships_added': result.get('relationships_added', 0),
                'extraction_summary': {
                    'total_entities': sum(
                        len(entities) for entities in 
                        result.get('extraction_result', {}).get('entities', {}).values()
                    ),
                    'total_relationships': len(
                        result.get('extraction_result', {}).get('relationships', [])
                    )
                }
            }), 200
            
        except Exception as e:
            logger.error(f"Add document to graph error: {str(e)}")
            return jsonify({'error': 'Internal server error'}), 500
    
    @app.route('/api/knowledge-graph/document-relationships/<document_id>', methods=['GET'])
    @require_auth
    def get_graph_document_relationships(document_id: str) -> Tuple[Dict[str, Any], int]:
        """
        Get document relationships from knowledge graph
        
        Headers:
            Authorization: Bearer <session_token>
            
        URL Parameters:
            document_id: Document ID to analyze
            
        Query Parameters:
            include_entities (bool, optional): Include entity details
            max_related (int, optional): Maximum related documents
            
        Returns:
            200: Document relationships and entities
            404: Document not found
            500: Error getting relationships
        """
        try:
            if not knowledge_graph:
                return jsonify({'error': 'Knowledge graph not available'}), 503
            
            include_entities = request.args.get('include_entities', 'true').lower() == 'true'
            max_related = request.args.get('max_related', 10, type=int)
            
            # Get relationships
            result = knowledge_graph.get_document_relationships(document_id)
            
            if not result.get('success'):
                error = result.get('error', 'Could not get relationships')
                if 'not found' in error.lower():
                    return jsonify({'error': error}), 404
                else:
                    return jsonify({'error': error}), 500
            
            response = {
                'success': True,
                'document_id': document_id,
                'related_documents': result.get('related_documents', [])[:max_related],
                'entity_count': result.get('entity_count', 0)
            }
            
            if include_entities:
                response['entities'] = result.get('direct_entities', [])
            
            return jsonify(response), 200
            
        except Exception as e:
            logger.error(f"Graph document relationships error: {str(e)}")
            return jsonify({'error': 'Internal server error'}), 500
    
    @app.route('/api/knowledge-graph/search-entities', methods=['POST'])
    @require_auth
    def search_graph_entities() -> Tuple[Dict[str, Any], int]:
        """
        Search entities in knowledge graph
        
        Headers:
            Authorization: Bearer <session_token>
            Content-Type: application/json
            
        Request Body:
            query (str): Search query
            entity_types (list, optional): Filter by entity types
            max_results (int, optional): Maximum results to return
            
        Returns:
            200: Entity search results
            400: Invalid request
            500: Search error
        """
        try:
            if not knowledge_graph:
                return jsonify({'error': 'Knowledge graph not available'}), 503
            
            data = request.get_json()
            if not data or 'query' not in data:
                return jsonify({'error': 'query is required'}), 400
            
            query = data['query']
            entity_types = data.get('entity_types')
            max_results = data.get('max_results', 20)
            
            # Search entities
            search_result = knowledge_graph.search_entities(query, entity_types)
            
            if not search_result.get('success'):
                return jsonify({'error': search_result.get('error', 'Search failed')}), 500
            
            results = search_result.get('results', [])[:max_results]
            
            return jsonify({
                'success': True,
                'query': query,
                'entity_types_filter': entity_types,
                'results': results,
                'total_found': search_result.get('total_found', 0),
                'returned_count': len(results)
            }), 200
            
        except Exception as e:
            logger.error(f"Entity search error: {str(e)}")
            return jsonify({'error': 'Internal server error'}), 500
    
    @app.route('/api/knowledge-graph/analytics', methods=['GET'])
    @require_auth
    def get_graph_analytics() -> Tuple[Dict[str, Any], int]:
        """
        Get knowledge graph analytics and metrics
        
        Headers:
            Authorization: Bearer <session_token>
            
        Query Parameters:
            include_centrality (bool, optional): Include centrality measures
            
        Returns:
            200: Graph analytics and statistics
            500: Error getting analytics
        """
        try:
            if not knowledge_graph:
                return jsonify({'error': 'Knowledge graph not available'}), 503
            
            include_centrality = request.args.get('include_centrality', 'false').lower() == 'true'
            
            # Get analytics
            analytics = knowledge_graph.get_graph_analytics()
            
            if 'error' in analytics:
                return jsonify({'error': analytics['error']}), 500
            
            return jsonify({
                'success': True,
                'analytics': analytics,
                'timestamp': analytics.get('metadata', {}).get('created')
            }), 200
            
        except Exception as e:
            logger.error(f"Graph analytics error: {str(e)}")
            return jsonify({'error': 'Internal server error'}), 500
    
    @app.route('/api/knowledge-graph/export', methods=['POST'])
    @require_auth
    def export_knowledge_graph() -> Tuple[Dict[str, Any], int]:
        """
        Export knowledge graph in specified format
        
        Headers:
            Authorization: Bearer <session_token>
            Content-Type: application/json
            
        Request Body:
            format (str): Export format ('json')
            include_metadata (bool, optional): Include metadata
            
        Returns:
            200: Exported graph data
            400: Invalid format
            500: Export error
        """
        try:
            if not knowledge_graph:
                return jsonify({'error': 'Knowledge graph not available'}), 503
            
            data = request.get_json() or {}
            format_type = data.get('format', 'json')
            include_metadata = data.get('include_metadata', True)
            
            if format_type not in ['json']:
                return jsonify({'error': f'Unsupported format: {format_type}'}), 400
            
            # Export graph
            export_result = knowledge_graph.export_graph(format_type)
            
            if not export_result.get('success'):
                return jsonify({'error': export_result.get('error', 'Export failed')}), 500
            
            response = {
                'success': True,
                'format': format_type,
                'graph_data': export_result['data']
            }
            
            if not include_metadata:
                response['graph_data'].pop('metadata', None)
            
            return jsonify(response), 200
            
        except Exception as e:
            logger.error(f"Graph export error: {str(e)}")
            return jsonify({'error': 'Internal server error'}), 500
    
    @app.route('/api/knowledge-graph/find-path', methods=['POST'])
    @require_auth
    def find_shortest_path() -> Tuple[Dict[str, Any], int]:
        """
        Find shortest path between two nodes in knowledge graph
        
        Headers:
            Authorization: Bearer <session_token>
            Content-Type: application/json
            
        Request Body:
            source_id (str): Source node ID
            target_id (str): Target node ID
            
        Returns:
            200: Shortest path information
            400: Invalid request
            404: No path found
            500: Error finding path
        """
        try:
            if not knowledge_graph:
                return jsonify({'error': 'Knowledge graph not available'}), 503
            
            data = request.get_json()
            if not data or 'source_id' not in data or 'target_id' not in data:
                return jsonify({'error': 'source_id and target_id are required'}), 400
            
            source_id = data['source_id']
            target_id = data['target_id']
            
            # Find path
            path_result = knowledge_graph.find_shortest_path(source_id, target_id)
            
            if not path_result.get('success'):
                error = path_result.get('error', 'Could not find path')
                if 'no path' in error.lower():
                    return jsonify({'error': error}), 404
                else:
                    return jsonify({'error': error}), 500
            
            return jsonify({
                'success': True,
                'source_id': source_id,
                'target_id': target_id,
                'path': path_result.get('path', []),
                'path_length': path_result.get('path_length', 0),
                'path_details': path_result.get('path_details', [])
            }), 200
            
        except Exception as e:
            logger.error(f"Find path error: {str(e)}")
            return jsonify({'error': 'Internal server error'}), 500
    
    # ========== UTILITY ENDPOINTS ==========
    
    @app.route('/api/enhanced-features/status', methods=['GET'])
    def get_enhanced_features_status() -> Tuple[Dict[str, Any], int]:
        """
        Get status of enhanced features
        
        Returns:
            200: Feature availability status
        """
        try:
            status = {
                'enhanced_file_processing': enhanced_processor is not None,
                'advanced_rag': advanced_rag is not None,
                'knowledge_graph': knowledge_graph is not None,
                'capabilities': {
                    'ocr_available': False,
                    'advanced_pdf': False,
                    'office_support': False,
                    'graph_analysis': False,
                    'relationship_analysis': False
                }
            }
            
            # Check capabilities if enhanced processor is available
            if enhanced_processor:
                try:
                    from PIL import Image
                    import pytesseract
                    status['capabilities']['ocr_available'] = True
                except ImportError:
                    pass
                
                try:
                    import pdfplumber
                    status['capabilities']['advanced_pdf'] = True
                except ImportError:
                    pass
                
                try:
                    from docx import Document
                    from pptx import Presentation
                    status['capabilities']['office_support'] = True
                except ImportError:
                    pass
            
            # Check graph capabilities
            if knowledge_graph:
                try:
                    import networkx as nx
                    status['capabilities']['graph_analysis'] = True
                except ImportError:
                    pass
            
            # Check relationship analysis capabilities
            if advanced_rag:
                try:
                    from sklearn.feature_extraction.text import TfidfVectorizer
                    status['capabilities']['relationship_analysis'] = True
                except ImportError:
                    pass
            
            return jsonify(status), 200
            
        except Exception as e:
            logger.error(f"Status check error: {str(e)}")
            return jsonify({'error': 'Internal server error'}), 500


def generate_code_recommendations(code_analysis: Dict[str, Any]) -> List[str]:
    """Generate code improvement recommendations based on analysis"""
    recommendations = []
    
    # Check complexity
    complexity = code_analysis.get('complexity', {})
    if complexity.get('complexity_score', 0) > 20:
        recommendations.append("Consider breaking down complex functions to improve maintainability")
    
    if complexity.get('max_nesting_level', 0) > 4:
        recommendations.append("High nesting levels detected - consider refactoring for better readability")
    
    # Check security issues
    security_issues = code_analysis.get('security_analysis', [])
    if security_issues:
        recommendations.append(f"Found {len(security_issues)} potential security issues - review and address")
    
    # Check statistics
    stats = code_analysis.get('statistics', {})
    comment_ratio = stats.get('comment_lines', 0) / max(stats.get('code_lines', 1), 1)
    if comment_ratio < 0.1:
        recommendations.append("Consider adding more comments to improve code documentation")
    
    # Check function/class counts
    if stats.get('functions_count', 0) == 0 and stats.get('classes_count', 0) == 0:
        recommendations.append("Consider organizing code into functions or classes for better structure")
    
    return recommendations[:5]  # Return top 5 recommendations