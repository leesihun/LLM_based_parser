"""
Topic Classifier Module
Classifies reviews by topics (battery, screen, camera, etc.) to enable topic-specific filtering.
Uses keyword-based classification for efficient topic detection.
"""

import logging
from typing import List, Dict, Set
import re

logger = logging.getLogger(__name__)


class TopicClassifier:
    """Classifier for detecting topics in cellphone reviews."""
    
    def __init__(self):
        """Initialize with predefined topic keywords."""
        self.topic_keywords = {
            "battery": [
                "battery", "power", "charge", "charging", "drain", "juice", "life", "lasting",
                "hours", "day", "dies", "dead", "mah", "percent", "%", "plug", "charger",
                "fast charging", "wireless charging", "battery life"
            ],
            "screen": [
                "screen", "display", "brightness", "color", "resolution", "pixel", "touch",
                "responsive", "size", "inch", "oled", "lcd", "amoled", "retina", "hd", "4k",
                "contrast", "viewing", "outdoor", "sunlight", "scratch", "cracked", "broken"
            ],
            "camera": [
                "camera", "photo", "picture", "image", "video", "lens", "zoom", "focus",
                "blur", "quality", "megapixel", "mp", "front camera", "back camera", "selfie",
                "portrait", "night mode", "flash", "recording", "optical", "digital"
            ],
            "performance": [
                "performance", "speed", "fast", "slow", "lag", "freeze", "crash", "smooth",
                "processor", "cpu", "gpu", "ram", "memory", "storage", "app", "game", "gaming",
                "multitask", "respond", "quick", "sluggish", "choppy"
            ],
            "design": [
                "design", "look", "appearance", "beautiful", "ugly", "premium", "cheap",
                "build quality", "material", "metal", "plastic", "glass", "weight", "heavy",
                "light", "thin", "thick", "compact", "size", "ergonomic", "comfortable"
            ],
            "audio": [
                "sound", "audio", "speaker", "volume", "loud", "quiet", "music", "call",
                "voice", "headphone", "earphone", "bluetooth", "noise", "quality", "bass",
                "treble", "clear", "muffled", "stereo", "mono"
            ],
            "software": [
                "software", "android", "ios", "update", "version", "ui", "interface",
                "settings", "feature", "bug", "glitch", "system", "operating", "smooth",
                "customize", "app", "notification", "keyboard", "launcher"
            ],
            "connectivity": [
                "wifi", "bluetooth", "cellular", "signal", "reception", "network", "data",
                "internet", "connection", "disconnect", "5g", "4g", "lte", "hotspot", "nfc",
                "gps", "location", "maps"
            ],
            "durability": [
                "durability", "durable", "fragile", "break", "broken", "crack", "scratch",
                "drop", "water", "resistant", "proof", "protection", "case", "cover",
                "damage", "wear", "tear", "quality", "build"
            ],
            "price": [
                "price", "cost", "expensive", "cheap", "affordable", "value", "money",
                "worth", "budget", "deal", "sale", "discount", "overpriced", "reasonable",
                "dollar", "$", "buy", "purchase"
            ]
        }
        
        # Compile regex patterns for each topic for faster matching
        self.topic_patterns = {}
        for topic, keywords in self.topic_keywords.items():
            # Create pattern that matches any of the keywords as whole words
            pattern = r'\b(?:' + '|'.join(re.escape(kw) for kw in keywords) + r')\b'
            self.topic_patterns[topic] = re.compile(pattern, re.IGNORECASE)
        
        logger.info(f"Topic classifier initialized with {len(self.topic_keywords)} topics")
    
    def classify_review(self, review_text: str) -> Dict[str, int]:
        """
        Classify a single review by topics.
        
        Args:
            review_text: The review text to classify
            
        Returns:
            Dictionary with topic names as keys and match counts as values
        """
        # Remove sentiment prefix if present
        clean_text = review_text
        if clean_text.startswith("[POSITIVE]") or clean_text.startswith("[NEGATIVE]"):
            clean_text = clean_text.split("]", 1)[1].strip()
        
        topic_matches = {}
        for topic, pattern in self.topic_patterns.items():
            matches = pattern.findall(clean_text)
            topic_matches[topic] = len(matches)
        
        return topic_matches
    
    def get_review_topics(self, review_text: str, min_matches: int = 1) -> List[str]:
        """
        Get list of topics for a single review.
        
        Args:
            review_text: The review text to classify
            min_matches: Minimum number of keyword matches required
            
        Returns:
            List of topic names that match the review
        """
        topic_matches = self.classify_review(review_text)
        return [topic for topic, count in topic_matches.items() if count >= min_matches]
    
    def filter_reviews_by_topic(self, reviews: List[str], topic: str, min_matches: int = 1) -> List[str]:
        """
        Filter reviews that match a specific topic.
        
        Args:
            reviews: List of review texts
            topic: Topic name to filter by
            min_matches: Minimum number of keyword matches required
            
        Returns:
            List of reviews that match the topic
        """
        if topic not in self.topic_patterns:
            logger.warning(f"Unknown topic: {topic}. Available topics: {list(self.topic_keywords.keys())}")
            return []
        
        matching_reviews = []
        pattern = self.topic_patterns[topic]
        
        for review in reviews:
            # Remove sentiment prefix if present
            clean_text = review
            if clean_text.startswith("[POSITIVE]") or clean_text.startswith("[NEGATIVE]"):
                clean_text = clean_text.split("]", 1)[1].strip()
            
            matches = len(pattern.findall(clean_text))
            if matches >= min_matches:
                matching_reviews.append(review)
        
        logger.info(f"Found {len(matching_reviews)} reviews matching topic '{topic}'")
        return matching_reviews
    
    def count_reviews_by_topic(self, reviews: List[str], topic: str, min_matches: int = 1) -> int:
        """
        Count reviews that match a specific topic.
        
        Args:
            reviews: List of review texts
            topic: Topic name to filter by
            min_matches: Minimum number of keyword matches required
            
        Returns:
            Number of reviews that match the topic
        """
        matching_reviews = self.filter_reviews_by_topic(reviews, topic, min_matches)
        return len(matching_reviews)
    
    def get_topic_distribution(self, reviews: List[str]) -> Dict[str, int]:
        """
        Get distribution of topics across all reviews.
        
        Args:
            reviews: List of review texts
            
        Returns:
            Dictionary with topic names as keys and counts as values
        """
        topic_counts = {topic: 0 for topic in self.topic_keywords.keys()}
        
        for review in reviews:
            topics = self.get_review_topics(review)
            for topic in topics:
                topic_counts[topic] += 1
        
        return topic_counts
    
    def get_available_topics(self) -> List[str]:
        """Get list of available topic names."""
        return list(self.topic_keywords.keys())
    
    def add_topic_keywords(self, topic: str, keywords: List[str]):
        """
        Add new keywords to an existing topic or create a new topic.
        
        Args:
            topic: Topic name
            keywords: List of keywords to add
        """
        if topic in self.topic_keywords:
            # Add to existing topic
            self.topic_keywords[topic].extend(keywords)
        else:
            # Create new topic
            self.topic_keywords[topic] = keywords
        
        # Recompile pattern
        pattern = r'\b(?:' + '|'.join(re.escape(kw) for kw in self.topic_keywords[topic]) + r')\b'
        self.topic_patterns[topic] = re.compile(pattern, re.IGNORECASE)
        
        logger.info(f"Updated topic '{topic}' with {len(keywords)} new keywords")