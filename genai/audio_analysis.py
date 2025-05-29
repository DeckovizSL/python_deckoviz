"""
Module for audio transcript analysis, including summarization and insights generation.
"""
import os
import re
import json
import logging
from typing import Dict, List, Any, Optional

import nltk
from nltk.tokenize import sent_tokenize
from nltk.corpus import stopwords
from nltk.probability import FreqDist
from transformers import pipeline, AutoTokenizer, AutoModelForSeq2SeqLM

# Set up logging
logger = logging.getLogger(__name__)

class TranscriptAnalyzer:
    """
    Analyzes transcripts to extract summaries, topics, and insights.
    """
    def __init__(self):
        """
        Initialize the TranscriptAnalyzer with required NLP models.
        """
        # Ensure required NLTK data is downloaded
        try:
            nltk.data.find('tokenizers/punkt')
        except LookupError:
            nltk.download('punkt')
        
        try:
            nltk.data.find('corpora/stopwords')
        except LookupError:
            nltk.download('stopwords')
        
        # Initialize summarization model
        try:
            self.summarizer_model = "facebook/bart-large-cnn"
            self.summarizer = pipeline("summarization", model=self.summarizer_model)
            logger.info("Summarization model loaded successfully")
        except Exception as e:
            logger.error(f"Error loading summarization model: {str(e)}")
            self.summarizer = None
        
        # Initialize sentiment analysis model
        try:
            self.sentiment_model = "distilbert-base-uncased-finetuned-sst-2-english"
            self.sentiment_analyzer = pipeline("sentiment-analysis", model=self.sentiment_model)
            logger.info("Sentiment analysis model loaded successfully")
        except Exception as e:
            logger.error(f"Error loading sentiment analysis model: {str(e)}")
            self.sentiment_analyzer = None
    
    def _preprocess_text(self, text: str) -> str:
        """
        Preprocess text for analysis.
        
        Args:
            text: The text to preprocess
            
        Returns:
            str: Preprocessed text
        """
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        # Remove special characters
        text = re.sub(r'[^\w\s\.\,\?\!]', '', text)
        return text
    
    def generate_summary(self, text: str, max_length: int = 150, min_length: int = 40) -> str:
        """
        Generate a summary of the transcript.
        
        Args:
            text: Transcript text to summarize
            max_length: Maximum length of summary in tokens
            min_length: Minimum length of summary in tokens
            
        Returns:
            str: Generated summary
        """
        if not text or len(text) < 100:
            logger.warning("Text too short for summarization")
            return text
        
        try:
            text = self._preprocess_text(text)
            
            # Handle long texts by chunking
            if len(text.split()) > 1024:
                chunks = self._chunk_text(text)
                chunk_summaries = []
                
                for chunk in chunks:
                    summary = self.summarizer(chunk, max_length=max_length//len(chunks), 
                                             min_length=min_length//len(chunks), 
                                             do_sample=False)
                    chunk_summaries.append(summary[0]['summary_text'])
                
                final_summary = " ".join(chunk_summaries)
                return final_summary
            else:
                summary = self.summarizer(text, max_length=max_length, 
                                         min_length=min_length, 
                                         do_sample=False)
                return summary[0]['summary_text']
        except Exception as e:
            logger.error(f"Error generating summary: {str(e)}")
            # Fallback to extractive summarization if model fails
            return self._extractive_summarize(text, int(min_length * 0.5))
    
    def _extractive_summarize(self, text: str, num_sentences: int = 3) -> str:
        """
        Create an extractive summary by selecting the most important sentences.
        
        Args:
            text: Text to summarize
            num_sentences: Number of sentences to include in summary
            
        Returns:
            str: Extractive summary
        """
        sentences = sent_tokenize(text)
        
        if len(sentences) <= num_sentences:
            return text
        
        # Remove stopwords
        stop_words = set(stopwords.words('english'))
        word_frequencies = {}
        
        for sentence in sentences:
            for word in nltk.word_tokenize(sentence.lower()):
                if word not in stop_words and word.isalnum():
                    if word not in word_frequencies:
                        word_frequencies[word] = 1
                    else:
                        word_frequencies[word] += 1
        
        # Normalize frequencies
        max_frequency = max(word_frequencies.values()) if word_frequencies else 1
        for word in word_frequencies:
            word_frequencies[word] /= max_frequency
        
        # Score sentences
        sentence_scores = {}
        for i, sentence in enumerate(sentences):
            for word in nltk.word_tokenize(sentence.lower()):
                if word in word_frequencies:
                    if i not in sentence_scores:
                        sentence_scores[i] = word_frequencies[word]
                    else:
                        sentence_scores[i] += word_frequencies[word]
        
        # Get top sentences
        top_sentence_indices = sorted(sentence_scores, key=sentence_scores.get, reverse=True)[:num_sentences]
        top_sentence_indices = sorted(top_sentence_indices)  # Sort by position in original text
        
        summary = " ".join([sentences[i] for i in top_sentence_indices])
        return summary
    
    def _chunk_text(self, text: str, max_chunk_size: int = 1000) -> List[str]:
        """
        Split text into chunks for processing.
        
        Args:
            text: Text to split
            max_chunk_size: Maximum number of words per chunk
            
        Returns:
            List[str]: List of text chunks
        """
        words = text.split()
        chunks = []
        
        for i in range(0, len(words), max_chunk_size):
            chunk = " ".join(words[i:i+max_chunk_size])
            chunks.append(chunk)
        
        return chunks
    
    def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """
        Analyze the sentiment of the transcript.
        
        Args:
            text: Transcript text to analyze
            
        Returns:
            Dict: Sentiment analysis results
        """
        if not text:
            return {"sentiment": "neutral", "score": 0.5}
        
        try:
            text = self._preprocess_text(text)
            
            # For long texts, analyze each paragraph and average the results
            paragraphs = text.split('\n\n')
            if len(paragraphs) > 1:
                positive_count = 0
                total_score = 0
                
                for paragraph in paragraphs:
                    if not paragraph.strip():
                        continue
                    
                    result = self.sentiment_analyzer(paragraph[:512])[0]
                    if result['label'] == 'POSITIVE':
                        positive_count += 1
                    total_score += result['score'] if result['label'] == 'POSITIVE' else 1 - result['score']
                
                avg_score = total_score / len(paragraphs) if paragraphs else 0.5
                sentiment = "positive" if positive_count > len(paragraphs) / 2 else "negative"
                
                return {
                    "sentiment": sentiment,
                    "score": avg_score
                }
            else:
                result = self.sentiment_analyzer(text[:512])[0]
                sentiment = "positive" if result['label'] == 'POSITIVE' else "negative"
                score = result['score'] if result['label'] == 'POSITIVE' else 1 - result['score']
                
                return {
                    "sentiment": sentiment.lower(),
                    "score": score
                }
        except Exception as e:
            logger.error(f"Error analyzing sentiment: {str(e)}")
            return {"sentiment": "neutral", "score": 0.5}
    
    def extract_topics(self, text: str, num_topics: int = 5) -> List[str]:
        """
        Extract key topics from the transcript.
        
        Args:
            text: Transcript text to analyze
            num_topics: Number of topics to extract
            
        Returns:
            List[str]: List of key topics
        """
        if not text:
            return []
        
        try:
            text = self._preprocess_text(text)
            stop_words = set(stopwords.words('english'))
            
            # Tokenize and filter words
            words = [word.lower() for word in nltk.word_tokenize(text) 
                    if word.lower() not in stop_words 
                    and word.isalpha() 
                    and len(word) > 3]
            
            # Find most common words
            fdist = FreqDist(words)
            topics = [word for word, _ in fdist.most_common(num_topics)]
            
            return topics
        except Exception as e:
            logger.error(f"Error extracting topics: {str(e)}")
            return []
    
    def generate_insights(self, text: str) -> Dict[str, Any]:
        """
        Generate comprehensive insights from transcript.
        
        Args:
            text: Transcript text to analyze
            
        Returns:
            Dict: Dictionary of insights including summary, sentiment, topics, etc.
        """
        if not text:
            return {
                "summary": "",
                "sentiment": {"sentiment": "neutral", "score": 0.5},
                "topics": [],
                "word_count": 0
            }
        
        insights = {}
        
        # Generate summary
        insights["summary"] = self.generate_summary(text)
        
        # Analyze sentiment
        insights["sentiment"] = self.analyze_sentiment(text)
        
        # Extract topics
        insights["topics"] = self.extract_topics(text)
        
        # Calculate statistics
        insights["word_count"] = len(text.split())
        
        return insights
