"""
RAG (Retrieval-Augmented Generation) functionality for chatting with summaries.
"""

import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import re
import json

from .summarizer import LLMSummarizer

logger = logging.getLogger(__name__)

@dataclass
class ChatMessage:
    """Represents a chat message."""
    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime

@dataclass
class SearchResult:
    """Represents a search result from summaries."""
    summary_file: Path
    relevant_content: str
    date: Optional[datetime]
    hashtag: str
    similarity_score: float

class SummaryRAG:
    """
    RAG system for chatting with Obsidian summaries.
    """
    
    def __init__(self, summaries_dir: Path, model: str = "llama2:7b"):
        """
        Initialize the RAG system.
        
        Args:
            summaries_dir: Directory containing summary files
            model: LLM model to use for generation
        """
        self.summaries_dir = Path(summaries_dir)
        self.model = model
        self.summarizer = LLMSummarizer(model)
        self.chat_history: List[ChatMessage] = []
        
        if not self.summaries_dir.exists():
            raise ValueError(f"Summaries directory does not exist: {summaries_dir}")
        
        logger.info(f"Initialized RAG system with summaries dir: {summaries_dir}")


    def search_summaries(self, query: str, limit: int = 5) -> List[SearchResult]:
        """
        Search through summaries for relevant content.
        
        Args:
            query: Search query
            limit: Maximum number of results to return
            
        Returns:
            List of SearchResult objects
        """
        results = []
        query_lower = query.lower()
        
        # Get all summary files
        summary_files = list(self.summaries_dir.glob("*.md"))
        
        for summary_file in summary_files:
            try:
                content = summary_file.read_text(encoding='utf-8')
                
                # TODO: improve this with a more sophisticated approach. For now, we'll use a simple keyword matching.
                relevance_score = self._calculate_relevance(content, query_lower)
                
                if relevance_score > 0:
                    # Extract metadata from filename or content
                    metadata = self._extract_metadata(summary_file, content)
                    
                    # Find most relevant snippet
                    relevant_content = self._extract_relevant_snippet(content, query_lower)
                    
                    results.append(SearchResult(
                        summary_file=summary_file,
                        relevant_content=relevant_content,
                        date=metadata.get('date'),
                        hashtag=metadata.get('hashtag', 'unknown'),
                        similarity_score=relevance_score
                    ))
                    
            except Exception as e:
                logger.warning(f"Failed to process {summary_file}: {e}")
                continue
        
        # Sort by relevance and limit results
        results.sort(key=lambda x: x.similarity_score, reverse=True)
        return results[:limit]    
    
    def _calculate_relevance(self, content: str, query: str) -> float:
        """
        Calculate relevance score between content and query.
        
        Args:
            content: Summary content
            query: Search query
            
        Returns:
            Relevance score (0.0 to 1.0)
        """
        content_lower = content.lower()
        query_words = query.split()
        
        # Simple word frequency scoring
        score = 0.0
        total_words = len(query_words)
        
        for word in query_words:
            if len(word) < 3:  # Skip short words
                continue
            count = content_lower.count(word)
            score += count
        
        # Normalize score
        if total_words > 0:
            score = score / (total_words * 10)  # Normalize by expected frequency
        
        return min(score, 1.0)
    
    
    def _extract_metadata(self, summary_file: Path, content: str) -> Dict[str, Any]:
        """
        Extract metadata from summary file.
        
        Args:
            summary_file: Path to summary file
            content: File content
            
        Returns:
            Dictionary with metadata
        """
        metadata = {}
        
        # Extract date from filename
        date_match = re.search(r'(\d{4}-\d{2}-\d{2})', summary_file.stem)
        if date_match:
            try:
                metadata['date'] = datetime.strptime(date_match.group(1), '%Y-%m-%d')
            except ValueError:
                pass
        
        # Extract hashtag from filename
        hashtag_match = re.search(r'#(\w+)', summary_file.stem)
        if hashtag_match:
            metadata['hashtag'] = hashtag_match.group(1)
        
        # Extract from frontmatter if present
        if content.startswith('---'):
            try:
                import yaml
                parts = content.split('---', 2)
                if len(parts) >= 3:
                    frontmatter = yaml.safe_load(parts[1]) or {}
                    metadata.update(frontmatter)
            except Exception:
                pass
        
        return metadata
    

    def _extract_relevant_snippet(self, content: str, query: str, max_length: int = 300) -> str:
        """
        Extract the most relevant snippet from content.
        
        Args:
            content: Full content
            query: Search query
            max_length: Maximum snippet length
            
        Returns:
            Relevant snippet
        """
        # Simple approach: find paragraph with most query words
        paragraphs = content.split('\n\n')
        best_paragraph = ""
        best_score = 0
        
        for paragraph in paragraphs:
            if len(paragraph.strip()) < 10:  # Skip very short paragraphs
                continue
            
            score = self._calculate_relevance(paragraph, query)
            if score > best_score:
                best_score = score
                best_paragraph = paragraph
        
        # Truncate if too long
        if len(best_paragraph) > max_length:
            best_paragraph = best_paragraph[:max_length] + "..."
        
        return best_paragraph.strip()
    

    def chat(self, message: str) -> str:
        """
        Chat with the summaries using RAG.
        
        Args:
            message: User message
            
        Returns:
            Assistant response
        """
        # Add user message to history
        self.chat_history.append(ChatMessage(
            role="user",
            content=message,
            timestamp=datetime.now()
        ))
        
        try:
            # Search for relevant content
            search_results = self.search_summaries(message)
            
            if not search_results:
                response = "I couldn't find any relevant information in the summaries for your question."
            else:
                # Generate response using LLM
                response = self._generate_response(message, search_results)
            
            # Add assistant response to history
            self.chat_history.append(ChatMessage(
                role="assistant",
                content=response,
                timestamp=datetime.now()
            ))
            
            return response
            
        except Exception as e:
            logger.error(f"Chat failed: {e}")
            error_response = f"Sorry, I encountered an error: {str(e)}"
            
            self.chat_history.append(ChatMessage(
                role="assistant",
                content=error_response,
                timestamp=datetime.now()
            ))
            
            return error_response
        

    def _generate_response(self, query: str, search_results: List[SearchResult]) -> str:
        """
        Generate response using LLM with retrieved context.
        
        Args:
            query: User query
            search_results: Retrieved relevant content
            
        Returns:
            Generated response
        """
        # Build context from search results
        context = self._build_context(search_results)
        
        # Create prompt
        prompt = f"""
        You are a helpful assistant that answers questions about Obsidian journal summaries.

        Context from summaries:
        {context}

        User question: {query}

        Please answer the question based on the context provided. If the information isn't in the context, say so. Be concise and helpful."""

        # Generate response
        try:
            response = self.summarizer._call_ollama(prompt)
            return response.strip()
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            return "I'm sorry, I couldn't generate a response due to a technical issue."    
        
    
    def _build_context(self, search_results: List[SearchResult]) -> str:
        """
        Build context string from search results.
        
        Args:
            search_results: List of search results
            
        Returns:
            Formatted context string
        """
        context_parts = []
        
        for i, result in enumerate(search_results, 1):
            date_str = result.date.strftime('%Y-%m-%d') if result.date else 'Unknown date'
            context_parts.append(f"Summary {i} ({date_str}, #{result.hashtag}):\n{result.relevant_content}\n")
        
        return "\n".join(context_parts)
    
    def get_chat_history(self) -> List[ChatMessage]:
        """Get chat history."""
        return self.chat_history.copy()
    
    def clear_chat_history(self):
        """Clear chat history."""
        self.chat_history.clear()