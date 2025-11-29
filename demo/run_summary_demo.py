#!/usr/bin/env python3
"""
Arrowhead Demo Script - Lightweight Summarizer

This script demonstrates the summarization capability of Arrowhead using a
deterministic heuristic approach (TextRank-based extractive summarization).
It does NOT require external LLM calls, making it suitable for CI/CD pipelines.

For production usage with LLMs, see the comments marked with "LLM INTEGRATION"
below to learn how to integrate with Ollama or OpenAI APIs.

Usage:
    python demo/run_summary_demo.py

Requirements:
    pip install nltk networkx

Optional (for enhanced summarization):
    pip install sumy
"""

import os
import sys
from pathlib import Path

# Add the src directory to the path for imports
src_path = Path(__file__).parent.parent / "src"
if src_path.exists():
    sys.path.insert(0, str(src_path))


def get_sample_note_path() -> Path:
    """Return the path to the sample note file."""
    return Path(__file__).parent / "sample_note.md"


def read_sample_note() -> str:
    """Read and return the content of the sample note."""
    note_path = get_sample_note_path()
    if not note_path.exists():
        raise FileNotFoundError(f"Sample note not found: {note_path}")
    return note_path.read_text(encoding="utf-8")


def simple_sentence_tokenize(text: str) -> list[str]:
    """
    Simple sentence tokenizer that splits on common sentence boundaries.
    Falls back to basic splitting if NLTK is not available.
    """
    try:
        import nltk
        try:
            return nltk.sent_tokenize(text)
        except LookupError:
            # Download punkt data if not available
            nltk.download("punkt", quiet=True)
            nltk.download("punkt_tab", quiet=True)
            return nltk.sent_tokenize(text)
    except ImportError:
        # Fallback: simple split on sentence-ending punctuation
        import re
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return [s.strip() for s in sentences if s.strip()]


def simple_word_tokenize(text: str) -> list[str]:
    """
    Simple word tokenizer.
    Falls back to basic splitting if NLTK is not available.
    """
    try:
        import nltk
        try:
            return nltk.word_tokenize(text.lower())
        except LookupError:
            nltk.download("punkt", quiet=True)
            nltk.download("punkt_tab", quiet=True)
            return nltk.word_tokenize(text.lower())
    except ImportError:
        # Fallback: simple split on whitespace and punctuation
        import re
        words = re.findall(r'\b\w+\b', text.lower())
        return words


def calculate_sentence_similarity(sent1: str, sent2: str) -> float:
    """
    Calculate similarity between two sentences using word overlap.
    Returns a value between 0 and 1.
    """
    words1 = set(simple_word_tokenize(sent1))
    words2 = set(simple_word_tokenize(sent2))
    
    if not words1 or not words2:
        return 0.0
    
    intersection = words1.intersection(words2)
    # Normalized overlap (Jaccard-like similarity)
    return len(intersection) / (len(words1) + len(words2) - len(intersection))


def textrank_summarize(text: str, num_sentences: int = 5) -> str:
    """
    Extractive summarization using TextRank algorithm.
    
    This is a deterministic, offline approach that doesn't require external APIs.
    It identifies the most important sentences based on their similarity to other
    sentences in the text (graph-based ranking).
    
    Args:
        text: The input text to summarize.
        num_sentences: Number of sentences to include in the summary.
    
    Returns:
        A summary consisting of the top-ranked sentences.
    """
    # Get sentences
    sentences = simple_sentence_tokenize(text)
    
    if len(sentences) <= num_sentences:
        return text
    
    # Filter out very short sentences (headers, list items without context)
    valid_sentences = [s for s in sentences if len(s.split()) >= 5]
    
    if len(valid_sentences) <= num_sentences:
        return "\n".join(valid_sentences[:num_sentences])
    
    try:
        import networkx as nx
        
        # Build similarity matrix
        n = len(valid_sentences)
        similarity_matrix = [[0.0] * n for _ in range(n)]
        
        for i in range(n):
            for j in range(n):
                if i != j:
                    similarity_matrix[i][j] = calculate_sentence_similarity(
                        valid_sentences[i], valid_sentences[j]
                    )
        
        # Create graph and run PageRank
        graph = nx.from_numpy_array(
            __import__("numpy").array(similarity_matrix)
        )
        scores = nx.pagerank(graph)
        
        # Rank sentences by score
        ranked_sentences = sorted(
            [(score, idx, sent) for idx, (sent, score) in enumerate(
                zip(valid_sentences, [scores[i] for i in range(n)])
            )],
            key=lambda x: x[0],
            reverse=True
        )
        
        # Get top sentences and sort by original order
        top_sentences = sorted(
            ranked_sentences[:num_sentences],
            key=lambda x: x[1]  # Sort by original index
        )
        
        return "\n".join(sent for _, _, sent in top_sentences)
        
    except ImportError:
        # Fallback: use first N sentences heuristic
        return fallback_summarize(text, num_sentences)


def fallback_summarize(text: str, num_sentences: int = 5) -> str:
    """
    Fallback summarizer using simple heuristics.
    
    Extracts the first few sentences plus any sentences that contain
    important keywords like "key", "important", "main", "summary", etc.
    
    Args:
        text: The input text to summarize.
        num_sentences: Number of sentences to include in the summary.
    
    Returns:
        A summary consisting of selected sentences.
    """
    sentences = simple_sentence_tokenize(text)
    
    if len(sentences) <= num_sentences:
        return text
    
    # Filter out very short sentences
    valid_sentences = [s for s in sentences if len(s.split()) >= 4]
    
    if not valid_sentences:
        return "\n".join(sentences[:num_sentences])
    
    # Keywords that indicate important sentences
    important_keywords = {
        "key", "important", "main", "summary", "conclusion",
        "result", "decided", "agreed", "priority", "focus"
    }
    
    # Score sentences
    scored = []
    for idx, sent in enumerate(valid_sentences):
        words = set(simple_word_tokenize(sent))
        keyword_score = len(words.intersection(important_keywords))
        position_score = 1.0 / (idx + 1)  # Earlier sentences get higher scores
        score = keyword_score + position_score
        scored.append((score, idx, sent))
    
    # Sort by score and take top N
    scored.sort(key=lambda x: x[0], reverse=True)
    top_sentences = sorted(scored[:num_sentences], key=lambda x: x[1])
    
    return "\n".join(sent for _, _, sent in top_sentences)


def summarize_with_llm(text: str, model: str = "llama2") -> str:
    """
    LLM INTEGRATION: Summarize text using a local LLM via Ollama.
    
    This function demonstrates how to integrate with Ollama for production usage.
    Uncomment and configure to use real LLM summarization.
    
    Prerequisites:
        1. Install Ollama: https://ollama.ai
        2. Pull a model: ollama pull llama2
        3. Ensure Ollama is running: ollama serve
    
    Environment Variables:
        OLLAMA_HOST: Ollama API endpoint (default: http://localhost:11434)
        OLLAMA_MODEL: Model to use (default: llama2)
    
    Args:
        text: The input text to summarize.
        model: The Ollama model to use.
    
    Returns:
        The LLM-generated summary.
    
    Example:
        >>> summary = summarize_with_llm("Your long text here...")
        >>> print(summary)
    """
    # LLM INTEGRATION: Uncomment the following code to enable Ollama integration
    #
    # import httpx
    # 
    # ollama_host = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
    # model_name = os.environ.get("OLLAMA_MODEL", model)
    # 
    # prompt = f'''Please summarize the following text concisely, 
    # highlighting the key points and main topics discussed:
    # 
    # {text}
    # 
    # Summary:'''
    # 
    # response = httpx.post(
    #     f"{ollama_host}/api/generate",
    #     json={"model": model_name, "prompt": prompt, "stream": False},
    #     timeout=120.0
    # )
    # response.raise_for_status()
    # return response.json()["response"]
    
    # For CI/demo purposes, use the deterministic summarizer
    return textrank_summarize(text)


def summarize_with_openai(text: str) -> str:
    """
    LLM INTEGRATION: Summarize text using OpenAI API.
    
    This function demonstrates how to integrate with OpenAI for production usage.
    Uncomment and configure to use OpenAI's GPT models.
    
    Environment Variables:
        OPENAI_API_KEY: Your OpenAI API key (required)
        OPENAI_MODEL: Model to use (default: gpt-3.5-turbo)
    
    Args:
        text: The input text to summarize.
    
    Returns:
        The LLM-generated summary.
    
    Example:
        >>> os.environ["OPENAI_API_KEY"] = "your-api-key"
        >>> summary = summarize_with_openai("Your long text here...")
        >>> print(summary)
    """
    # LLM INTEGRATION: Uncomment the following code to enable OpenAI integration
    #
    # from openai import OpenAI
    # 
    # api_key = os.environ.get("OPENAI_API_KEY")
    # if not api_key:
    #     raise ValueError("OPENAI_API_KEY environment variable is required")
    # 
    # client = OpenAI(api_key=api_key)
    # model = os.environ.get("OPENAI_MODEL", "gpt-3.5-turbo")
    # 
    # response = client.chat.completions.create(
    #     model=model,
    #     messages=[
    #         {"role": "system", "content": "You are a helpful assistant that summarizes text concisely."},
    #         {"role": "user", "content": f"Please summarize the following text:\n\n{text}"}
    #     ],
    #     max_tokens=500
    # )
    # return response.choices[0].message.content
    
    # For CI/demo purposes, use the deterministic summarizer
    return textrank_summarize(text)


def main() -> None:
    """Main entry point for the demo script."""
    print("=" * 60)
    print("Arrowhead Demo - Obsidian Note Summarizer")
    print("=" * 60)
    print()
    
    # Read the sample note
    print("📄 Reading sample note...")
    try:
        note_content = read_sample_note()
        print(f"   Loaded {len(note_content)} characters from sample_note.md")
    except FileNotFoundError as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
    
    print()
    print("-" * 60)
    print("📝 Original Note Preview (first 500 chars):")
    print("-" * 60)
    print(note_content[:500] + "..." if len(note_content) > 500 else note_content)
    
    print()
    print("-" * 60)
    print("🎯 Generating Summary (using TextRank algorithm)...")
    print("-" * 60)
    print()
    
    # Generate summary using deterministic method
    summary = textrank_summarize(note_content, num_sentences=5)
    
    print("📋 Summary:")
    print()
    print(summary)
    print()
    print("=" * 60)
    print("✅ Demo completed successfully!")
    print()
    print("💡 To use with a real LLM, see the comments in run_summary_demo.py")
    print("   for instructions on configuring Ollama or OpenAI integration.")
    print("=" * 60)
    
    # Return the summary for testing purposes
    return summary


if __name__ == "__main__":
    main()
