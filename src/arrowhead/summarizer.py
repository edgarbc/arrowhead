"""
LLM integration and prompt management for summarization.
"""

import subprocess
import json
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime
import time

from .parser import JournalEntry

logger = logging.getLogger(__name__)

@dataclass
class SummarizationRequest:
    """Represents a summarization request to the LLM."""
    entries: List[JournalEntry]
    hashtag: str
    start_date: Optional[datetime]
    end_date: Optional[datetime]
    batch_id: int
    total_batches: int

@dataclass
class SummarizationResponse:
    """Represents a response from the LLM."""
    content: str
    model: str
    request_time: float
    tokens_used: Optional[int] = None
    error: Optional[str] = None

class LLMSummarizer:
    """
    Handles LLM integration for summarization using Ollama.
    """
    
    def __init__(self, model: str = "llama2:7b", ollama_host: str = "http://localhost:11434"):
        """
        Initialize the summarizer.
        
        Args:
            model: LLM model to use (e.g., "llama2:7b", "mistral:7b", "gpt-4o-mini")
            ollama_host: Ollama server host and port
        """
        self.model = model
        self.ollama_host = ollama_host
        self.is_local_model = not model.startswith(("gpt-", "claude-"))
        
        # Prompt templates
        self.system_prompt = self._get_system_prompt()
        self.user_prompt_template = self._get_user_prompt_template()
        
        logger.info(f"Initialized summarizer with model: {model}")
        logger.info(f"Local model: {self.is_local_model}")
    
    def summarize_batch(self, entries: List[JournalEntry], hashtag: str, 
                       start_date: Optional[datetime] = None, 
                       end_date: Optional[datetime] = None,
                       batch_id: int = 1, total_batches: int = 1) -> SummarizationResponse:
        """
        Summarize a batch of journal entries.
        
        Args:
            entries: List of journal entries to summarize
            hashtag: Target hashtag for context
            start_date: Start of date range
            end_date: End of date range
            batch_id: Current batch number
            total_batches: Total number of batches
            
        Returns:
            SummarizationResponse with the summary content
        """
        if not entries:
            return SummarizationResponse(
                content="No entries to summarize.",
                model=self.model,
                request_time=0.0
            )
        
        # Create summarization request
        request = SummarizationRequest(
            entries=entries,
            hashtag=hashtag,
            start_date=start_date,
            end_date=end_date,
            batch_id=batch_id,
            total_batches=total_batches
        )
        
        # Generate prompt
        prompt = self._generate_prompt(request)
        
        # Call LLM
        start_time = time.time()
        try:
            if self.is_local_model:
                response = self._call_ollama(prompt)
            else:
                response = self._call_openai(prompt)
            
            request_time = time.time() - start_time
            
            return SummarizationResponse(
                content=response,
                model=self.model,
                request_time=request_time
            )
            
        except Exception as e:
            request_time = time.time() - start_time
            logger.error(f"Summarization failed: {e}")
            
            return SummarizationResponse(
                content="",
                model=self.model,
                request_time=request_time,
                error=str(e)
            )
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for summarization."""
        return """You are a helpful assistant that creates concise, well-structured summaries of journal entries.

Your task is to summarize journal entries tagged with a specific hashtag, focusing on:
- Key activities and events
- Important decisions or insights
- Patterns or recurring themes
- Action items or follow-ups

Guidelines:
- Be concise but comprehensive
- Use bullet points for clarity
- Group related items together
- Maintain chronological order when relevant
- Focus on actionable insights
- Use professional but friendly tone

Format your response as clean markdown with appropriate headings and bullet points."""
    
    def _get_user_prompt_template(self) -> str:
        """Get the user prompt template."""
        return """Please summarize the following journal entries tagged with #{hashtag}:

**Date Range**: {date_range}
**Batch**: {batch_info}
**Total Entries**: {entry_count}

{entries_text}

Please provide a structured summary that captures the key points, themes, and insights from these entries."""
    
    def _generate_prompt(self, request: SummarizationRequest) -> str:
        """
        Generate the complete prompt for summarization.
        
        Args:
            request: SummarizationRequest object
            
        Returns:
            Formatted prompt string
        """
        # Format date range
        if request.start_date and request.end_date:
            date_range = f"{request.start_date.strftime('%Y-%m-%d')} to {request.end_date.strftime('%Y-%m-%d')}"
        else:
            date_range = "All dates"
        
        # Format batch info
        if request.total_batches > 1:
            batch_info = f"Batch {request.batch_id} of {request.total_batches}"
        else:
            batch_info = "Single batch"
        
        # Format entries
        entries_text = self._format_entries(request.entries)
        
        # Generate user prompt
        user_prompt = self.user_prompt_template.format(
            hashtag=request.hashtag,
            date_range=date_range,
            batch_info=batch_info,
            entry_count=len(request.entries),
            entries_text=entries_text
        )
        
        return user_prompt
    
    def _format_entries(self, entries: List[JournalEntry]) -> str:
        """
        Format journal entries for the prompt.
        
        Args:
            entries: List of journal entries
            
        Returns:
            Formatted string representation
        """
        formatted_entries = []
        
        for entry in entries:
            # Format date
            if entry.date:
                date_str = entry.date.strftime('%Y-%m-%d')
            else:
                date_str = "Unknown date"
            
            # Format content (limit length to avoid token limits)
            content = entry.content[:1000]  # Limit to first 1000 chars
            if len(entry.content) > 1000:
                content += "... [truncated]"
            
            # Create entry text
            entry_text = f"**{date_str} - {entry.title}**\n{content}"
            formatted_entries.append(entry_text)
        
        return "\n\n---\n\n".join(formatted_entries)
    
    def _call_ollama(self, prompt: str) -> str:
        """
        Call Ollama API for summarization.
        
        Args:
            prompt: Complete prompt to send
            
        Returns:
            Response content from Ollama
        """
        try:
            # Prepare the request payload
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.3,  # Lower temperature for more consistent summaries
                    "top_p": 0.9,
                    "max_tokens": 2000
                }
            }
            
            # Make the API call
            import httpx
            with httpx.Client(timeout=60.0) as client:
                response = client.post(
                    f"{self.ollama_host}/api/generate",
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )
                response.raise_for_status()
                
                result = response.json()
                return result.get("response", "").strip()
                
        except Exception as e:
            logger.error(f"Ollama API call failed: {e}")
            raise
    
    def _call_openai(self, prompt: str) -> str:
        """
        Call OpenAI API for summarization (fallback for non-local models).
        
        Args:
            prompt: Complete prompt to send
            
        Returns:
            Response content from OpenAI
        """
        try:
            import openai
            
            # Set API key from environment
            import os
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY environment variable not set")
            
            client = openai.OpenAI(api_key=api_key)
            
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=2000
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"OpenAI API call failed: {e}")
            raise
    
    def test_connection(self) -> bool:
        """
        Test the connection to the LLM service.
        
        Returns:
            True if connection is successful
        """
        try:
            if self.is_local_model:
                # Test Ollama connection
                import httpx
                with httpx.Client(timeout=10.0) as client:
                    response = client.get(f"{self.ollama_host}/api/tags")
                    response.raise_for_status()
                    
                    # Check if model is available
                    models = response.json().get("models", [])
                    model_names = [model.get("name", "") for model in models]
                    
                    if self.model not in model_names:
                        logger.warning(f"Model {self.model} not found in available models: {model_names}")
                        return False
                    
                    return True
            else:
                # Test OpenAI connection
                import openai
                import os
                api_key = os.getenv("OPENAI_API_KEY")
                if not api_key:
                    logger.error("OPENAI_API_KEY not set")
                    return False
                
                client = openai.OpenAI(api_key=api_key)
                client.models.list()  # Simple API call to test connection
                return True
                
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the current model.
        
        Returns:
            Dictionary with model information
        """
        info = {
            "model": self.model,
            "is_local": self.is_local_model,
            "host": self.ollama_host if self.is_local_model else "OpenAI API"
        }
        
        if self.is_local_model:
            try:
                import httpx
                with httpx.Client(timeout=10.0) as client:
                    response = client.get(f"{self.ollama_host}/api/tags")
                    response.raise_for_status()
                    
                    models = response.json().get("models", [])
                    for model in models:
                        if model.get("name") == self.model:
                            info.update({
                                "size": model.get("size"),
                                "modified_at": model.get("modified_at"),
                                "digest": model.get("digest")
                            })
                            break
            except Exception as e:
                logger.warning(f"Could not get model info: {e}")
        
        return info