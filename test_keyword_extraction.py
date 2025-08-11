#!/usr/bin/env python3
"""
Test Suite for Keyword Extraction Functionality
Tests the keyword extraction system and its integration with web search
"""

import sys
import os
import json
from typing import Dict, List

# Add src directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

try:
    from src.keyword_extractor import KeywordExtractor
    from src.web_search_feature import WebSearchFeature
    from core.llm_client import LLMClient
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure you're running this from the project root directory")
    sys.exit(1)


class TestKeywordExtraction:
    """Comprehensive test suite for keyword extraction"""
    
    def __init__(self):
        """Initialize test suite"""
        self.test_cases = self._load_test_cases()
        self.results = []
        
        # Load configuration
        config_path = "config/search_config.json"
        self.config = {}
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                self.config = json.load(f)
        
        print("Keyword Extraction Test Suite")
        print("=" * 60)
        print(f"Loaded {len(self.test_cases)} test cases")
        print()
    
    def _load_test_cases(self) -> List[Dict]:
        """Load test cases for keyword extraction"""
        return [
            {
                'name': 'Technical Query - Machine Learning',
                'input': 'How can I implement machine learning algorithms for natural language processing in Python?',
                'expected_keywords': ['machine learning', 'algorithms', 'natural language processing', 'python'],
                'expected_min_keywords': 4,
                'description': 'Should extract technical terms and programming language'
            },
            {
                'name': 'Web Development Query',
                'input': 'What are the best practices for React component architecture and state management?',
                'expected_keywords': ['react', 'component', 'architecture', 'state management'],
                'expected_min_keywords': 3,
                'description': 'Should identify React-specific terms'
            },
            {
                'name': 'DevOps Infrastructure Query',
                'input': 'Can you help me understand Docker containerization and Kubernetes deployment strategies?',
                'expected_keywords': ['docker', 'containerization', 'kubernetes', 'deployment'],
                'expected_min_keywords': 3,
                'description': 'Should extract DevOps and infrastructure terms'
            },
            {
                'name': 'Database Query',
                'input': 'I need help with SQL database optimization and query performance tuning',
                'expected_keywords': ['sql', 'database', 'optimization', 'query', 'performance'],
                'expected_min_keywords': 4,
                'description': 'Should identify database-related terms'
            },
            {
                'name': 'API Design Query',
                'input': 'Show me examples of REST API design patterns using Express.js and Node.js',
                'expected_keywords': ['rest', 'api', 'design', 'patterns', 'express', 'node'],
                'expected_min_keywords': 4,
                'description': 'Should extract API and framework terms'
            },
            {
                'name': 'Generic Question',
                'input': 'What is the weather like today?',
                'expected_keywords': ['weather', 'today'],
                'expected_min_keywords': 1,
                'description': 'Should handle simple, non-technical queries'
            },
            {
                'name': 'Long Verbose Query',
                'input': 'I am looking for comprehensive tutorials and documentation that can help me understand how to build scalable microservices architecture using cloud native technologies like Docker containers and Kubernetes orchestration for enterprise applications',
                'expected_keywords': ['tutorials', 'documentation', 'microservices', 'architecture', 'cloud', 'docker', 'kubernetes', 'enterprise'],
                'expected_min_keywords': 5,
                'description': 'Should extract key terms from verbose input'
            },
            {
                'name': 'Mixed Case and Punctuation',
                'input': 'How do I use TensorFlow and PyTorch for deep-learning models? Need Python examples!',
                'expected_keywords': ['tensorflow', 'pytorch', 'deep learning', 'models', 'python'],
                'expected_min_keywords': 4,
                'description': 'Should handle mixed case and punctuation'
            }
        ]
    
    def run_all_tests(self):
        """Run all test suites"""
        print("Running Keyword Extraction Tests...")
        print()
        
        # Test 1: Basic keyword extraction
        self._test_basic_extraction()
        
        # Test 2: Different extraction methods
        self._test_extraction_methods()
        
        # Test 3: Query optimization
        self._test_query_optimization()
        
        # Test 4: Web search integration
        self._test_web_search_integration()
        
        # Test 5: Configuration handling
        self._test_configuration()
        
        # Test 6: Edge cases
        self._test_edge_cases()
        
        # Print summary
        self._print_test_summary()
    
    def _test_basic_extraction(self):
        """Test basic keyword extraction functionality"""
        print("1. Basic Keyword Extraction Tests")
        print("-" * 40)
        
        # Test with default configuration
        extractor = KeywordExtractor({
            'extraction_methods': ['rule_based', 'tfidf'],
            'max_keywords': 10,
            'min_keyword_length': 2
        })
        
        for test_case in self.test_cases:
            try:
                result = extractor.extract_keywords(test_case['input'])
                keywords = result.get('keywords', [])
                
                # Check if minimum expected keywords are found
                success = len(keywords) >= test_case['expected_min_keywords']
                
                # Check if expected keywords are present
                keywords_lower = [kw.lower() for kw in keywords]
                expected_found = sum(1 for exp_kw in test_case['expected_keywords'] 
                                   if any(exp_kw.lower() in kw_lower for kw_lower in keywords_lower))
                
                coverage = expected_found / len(test_case['expected_keywords']) * 100
                
                self.results.append({
                    'test': 'Basic Extraction',
                    'case': test_case['name'],
                    'success': success,
                    'coverage': coverage,
                    'keywords_found': len(keywords),
                    'expected_min': test_case['expected_min_keywords']
                })
                
                status = "PASS" if success else "FAIL"
                print(f"  {status}: {test_case['name']}")
                print(f"    Input: {test_case['input'][:50]}...")
                print(f"    Keywords: {keywords[:5]}")
                print(f"    Found: {len(keywords)}, Expected min: {test_case['expected_min_keywords']}")
                print(f"    Coverage: {coverage:.1f}%")
                print()
                
            except Exception as e:
                print(f"  ERROR: {test_case['name']} - {str(e)}")
                self.results.append({
                    'test': 'Basic Extraction',
                    'case': test_case['name'],
                    'success': False,
                    'error': str(e)
                })
    
    def _test_extraction_methods(self):
        """Test different extraction methods"""
        print("2. Extraction Methods Comparison")
        print("-" * 40)
        
        methods_to_test = [
            (['rule_based'], 'Rule-based only'),
            (['tfidf'], 'TF-IDF only'),
            (['rule_based', 'tfidf'], 'Combined methods')
        ]
        
        sample_query = self.test_cases[0]['input']  # Use first test case
        
        for methods, method_name in methods_to_test:
            try:
                extractor = KeywordExtractor({
                    'extraction_methods': methods,
                    'max_keywords': 8
                })
                
                result = extractor.extract_keywords(sample_query)
                keywords = result.get('keywords', [])
                extraction_results = result.get('extraction_results', {})
                
                print(f"  {method_name}:")
                print(f"    Methods used: {methods}")
                print(f"    Keywords found: {len(keywords)}")
                print(f"    Top keywords: {keywords[:5]}")
                print(f"    Extraction methods results: {list(extraction_results.keys())}")
                print()
                
                self.results.append({
                    'test': 'Method Comparison',
                    'method': method_name,
                    'success': len(keywords) > 0,
                    'keywords_count': len(keywords)
                })
                
            except Exception as e:
                print(f"  ERROR: {method_name} - {str(e)}")
    
    def _test_query_optimization(self):
        """Test query optimization and generation"""
        print("3. Query Optimization Tests")
        print("-" * 40)
        
        extractor = KeywordExtractor({
            'extraction_methods': ['rule_based', 'tfidf'],
            'query_expansion': True,
            'max_keywords': 8
        })
        
        for test_case in self.test_cases[:3]:  # Test first 3 cases
            try:
                result = extractor.extract_keywords(test_case['input'])
                queries = result.get('queries', [])
                
                success = len(queries) > 0 and len(queries[0]) > 0
                
                print(f"  {test_case['name']}:")
                print(f"    Original: {test_case['input'][:60]}...")
                print(f"    Generated queries ({len(queries)}):")
                for i, query in enumerate(queries, 1):
                    print(f"      {i}. {query}")
                print(f"    Status: {'PASS' if success else 'FAIL'}")
                print()
                
                self.results.append({
                    'test': 'Query Optimization',
                    'case': test_case['name'],
                    'success': success,
                    'queries_generated': len(queries)
                })
                
            except Exception as e:
                print(f"  ERROR: {test_case['name']} - {str(e)}")
    
    def _test_web_search_integration(self):
        """Test integration with web search feature"""
        print("4. Web Search Integration Tests")
        print("-" * 40)
        
        try:
            # Create web search feature with keyword extraction
            web_config = self.config.get('web_search', {})
            web_search = WebSearchFeature(web_config)
            
            # Test enabling/disabling keyword extraction
            print("  Testing keyword extraction control:")
            web_search.enable_keyword_extraction()
            print(f"    Enabled: {web_search.use_keyword_extraction}")
            
            web_search.disable_keyword_extraction()
            print(f"    Disabled: {web_search.use_keyword_extraction}")
            
            web_search.enable_keyword_extraction()  # Re-enable for testing
            
            # Test search with keyword extraction (without actual web search)
            print("\n  Testing search query preparation:")
            test_query = "How to implement machine learning algorithms in Python"
            
            # Mock the search to avoid actual web requests
            original_search = web_search.searcher.search
            web_search.searcher.search = lambda q, max_r: [
                {'title': 'Mock Result', 'snippet': 'Mock snippet', 'url': 'http://example.com'}
            ]
            
            try:
                result = web_search.search_web(test_query, max_results=3, format_for_llm=True)
                
                print(f"    Query: {test_query}")
                print(f"    Keyword extraction used: {result.get('keyword_extraction_used', False)}")
                print(f"    Queries tried: {result.get('queries_tried', [])}")
                print(f"    Successful query: {result.get('successful_query', 'None')}")
                print(f"    Results found: {result.get('result_count', 0)}")
                
                success = result.get('success', False)
                print(f"    Status: {'PASS' if success else 'FAIL'}")
                
                self.results.append({
                    'test': 'Web Search Integration',
                    'success': success,
                    'keyword_extraction_used': result.get('keyword_extraction_used', False)
                })
                
            finally:
                # Restore original search method
                web_search.searcher.search = original_search
                
        except Exception as e:
            print(f"  ERROR: Web search integration test failed - {str(e)}")
            self.results.append({
                'test': 'Web Search Integration',
                'success': False,
                'error': str(e)
            })
        
        print()
    
    def _test_configuration(self):
        """Test configuration handling"""
        print("5. Configuration Tests")
        print("-" * 40)
        
        # Test different configurations
        configs = [
            ({}, 'Default configuration'),
            ({'max_keywords': 5}, 'Limited keywords'),
            ({'min_keyword_length': 4}, 'Longer minimum length'),
            ({'extraction_methods': ['rule_based']}, 'Single method'),
            ({'query_expansion': False}, 'No query expansion')
        ]
        
        test_input = "Python machine learning tutorial with examples"
        
        for config, config_name in configs:
            try:
                extractor = KeywordExtractor(config)
                result = extractor.extract_keywords(test_input)
                keywords = result.get('keywords', [])
                
                print(f"  {config_name}:")
                print(f"    Config: {config}")
                print(f"    Keywords: {keywords}")
                print(f"    Count: {len(keywords)}")
                print()
                
                self.results.append({
                    'test': 'Configuration',
                    'config': config_name,
                    'success': True,
                    'keywords_count': len(keywords)
                })
                
            except Exception as e:
                print(f"  ERROR: {config_name} - {str(e)}")
                self.results.append({
                    'test': 'Configuration',
                    'config': config_name,
                    'success': False,
                    'error': str(e)
                })
    
    def _test_edge_cases(self):
        """Test edge cases and error handling"""
        print("6. Edge Cases and Error Handling")
        print("-" * 40)
        
        extractor = KeywordExtractor({
            'extraction_methods': ['rule_based'],
            'max_keywords': 5
        })
        
        edge_cases = [
            ('', 'Empty string'),
            ('   ', 'Whitespace only'),
            ('a b c', 'Very short words'),
            ('THE THE THE THE THE', 'All stop words'),
            ('123 456 789', 'Numbers only'),
            ('!@# $%^ &*()', 'Special characters only'),
            ('A' * 1000, 'Very long input'),
            ('How? What? When? Where? Why?', 'Question words only')
        ]
        
        for test_input, case_name in edge_cases:
            try:
                result = extractor.extract_keywords(test_input)
                keywords = result.get('keywords', [])
                queries = result.get('queries', [])
                
                # For edge cases, we mainly test that it doesn't crash
                success = isinstance(keywords, list) and isinstance(queries, list)
                
                print(f"  {case_name}:")
                print(f"    Input: {repr(test_input[:30])}")
                print(f"    Keywords: {keywords}")
                print(f"    Queries: {queries}")
                print(f"    Status: {'PASS' if success else 'FAIL'}")
                print()
                
                self.results.append({
                    'test': 'Edge Cases',
                    'case': case_name,
                    'success': success,
                    'keywords_count': len(keywords)
                })
                
            except Exception as e:
                print(f"  ERROR: {case_name} - {str(e)}")
                self.results.append({
                    'test': 'Edge Cases',
                    'case': case_name,
                    'success': False,
                    'error': str(e)
                })
    
    def _print_test_summary(self):
        """Print test summary and statistics"""
        print("=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.results)
        passed_tests = sum(1 for result in self.results if result.get('success', False))
        failed_tests = total_tests - passed_tests
        
        print(f"Total tests run: {total_tests}")
        print(f"Passed: {passed_tests} ({passed_tests/total_tests*100:.1f}%)")
        print(f"Failed: {failed_tests} ({failed_tests/total_tests*100:.1f}%)")
        print()
        
        # Group results by test type
        test_types = {}
        for result in self.results:
            test_type = result['test']
            if test_type not in test_types:
                test_types[test_type] = {'total': 0, 'passed': 0}
            test_types[test_type]['total'] += 1
            if result.get('success', False):
                test_types[test_type]['passed'] += 1
        
        print("Results by test type:")
        for test_type, stats in test_types.items():
            pass_rate = stats['passed'] / stats['total'] * 100
            print(f"  {test_type}: {stats['passed']}/{stats['total']} ({pass_rate:.1f}%)")
        
        print()
        
        # Show failed tests
        failed_results = [r for r in self.results if not r.get('success', False)]
        if failed_results:
            print("Failed tests:")
            for result in failed_results:
                test_id = f"{result['test']} - {result.get('case', result.get('config', result.get('method', 'Unknown')))}"
                error = result.get('error', 'Test failed')
                print(f"  ❌ {test_id}: {error}")
        else:
            print("🎉 All tests passed!")
        
        print()
        
        # Performance insights
        keyword_counts = [r.get('keywords_count', 0) for r in self.results if 'keywords_count' in r]
        if keyword_counts:
            avg_keywords = sum(keyword_counts) / len(keyword_counts)
            print(f"Average keywords extracted: {avg_keywords:.1f}")
        
        coverage_scores = [r.get('coverage', 0) for r in self.results if 'coverage' in r]
        if coverage_scores:
            avg_coverage = sum(coverage_scores) / len(coverage_scores)
            print(f"Average keyword coverage: {avg_coverage:.1f}%")


def main():
    """Run the keyword extraction tests"""
    tester = TestKeywordExtraction()
    tester.run_all_tests()


if __name__ == "__main__":
    main()