"""
Semantic chunking module for tender analyzer application.
"""

import os
from pathlib import Path
from loguru import logger
import tempfile
import numpy as np
import re

from langchain.text_splitter import RecursiveCharacterTextSplitter
from utils.error_handler import error_handler, ChunkingError
from utils.config import Config

# Simplified implementation for FAISS vector store
class SimplifiedVectorStore:
    def __init__(self, documents, embedding_function=None):
        """Initialize with documents and optional embedding function"""
        self.documents = documents
        self.document_texts = [doc.page_content for doc in documents]
        logger.debug(f"Created SimplifiedVectorStore with {len(documents)} documents")
        
    def similarity_search(self, query, k=5):
        """
        Simplified search that finds relevant documents based on keyword matching
        rather than vector similarity. This is a fallback when we can't use FAISS.
        
        Args:
            query (str): The search query
            k (int): Number of results to return
            
        Returns:
            list: List of documents most relevant to the query
        """
        logger.debug(f"Performing simplified search for: {query}")
        
        # Extract keywords from query
        keywords = re.findall(r'\b\w+\b', query.lower())
        keywords = [k for k in keywords if len(k) > 3]  # Filter short words
        
        if not keywords:
            logger.warning("No meaningful keywords found in query")
            return self.documents[:k]  # Return first k documents
        
        # Score documents based on keyword matches
        scores = []
        for i, text in enumerate(self.document_texts):
            text_lower = text.lower()
            score = sum(1 for keyword in keywords if keyword in text_lower)
            scores.append((i, score))
        
        # Sort by score descending
        scores.sort(key=lambda x: x[1], reverse=True)
        
        # Get top k documents
        top_docs = [self.documents[i] for i, _ in scores[:k]]
        
        logger.debug(f"Found {len(top_docs)} relevant documents")
        return top_docs


class SemanticChunker:
    """
    Class to perform semantic chunking and embedding of text.
    """
    
    def __init__(self):
        """Initialize the semantic chunker with default settings."""
        self.chunk_size = Config.CHUNK_SIZE
        self.chunk_overlap = Config.CHUNK_OVERLAP
        self.temp_dir = None
        logger.debug("SemanticChunker initialized")
        
    @error_handler
    def process(self, text):
        """
        Process text by chunking and embedding it.
        
        Args:
            text (str): The text to process.
            
        Returns:
            SimplifiedVectorStore: Vector store containing the chunks.
        """
        if not text or len(text.strip()) == 0:
            raise ChunkingError("Cannot process empty text")
        
        # Create chunks of the text
        chunks = self._create_chunks(text)
        logger.info(f"Created {len(chunks)} chunks from input text")
        
        # Create vector store
        vector_store = self._create_vector_store(chunks)
        logger.info("Created vector store from chunks")
        
        return vector_store
    
    @error_handler
    def _create_chunks(self, text):
        """
        Create semantic chunks from text.
        
        Args:
            text (str): The text to chunk.
            
        Returns:
            list: List of text chunks.
        """
        logger.debug(f"Creating chunks with size={self.chunk_size}, overlap={self.chunk_overlap}")
        
        # Create semantic chunks
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
        
        chunks = text_splitter.create_documents([text])
        
        # Log chunk information (simplified to avoid logger.level() issues)
        for i, chunk in enumerate(chunks):
            logger.debug(f"Chunk {i+1}/{len(chunks)}: {len(chunk.page_content)} chars")
                
        return chunks
    
    @error_handler
    def _create_vector_store(self, chunks):
        """
        Create a simplified vector store from chunks.
        
        Args:
            chunks (list): List of document chunks.
            
        Returns:
            SimplifiedVectorStore: Vector store containing the chunks.
        """
        try:
            # Create a simplified vector store
            logger.debug("Creating simplified vector store")
            vector_store = SimplifiedVectorStore(chunks)
            
            return vector_store
                
        except Exception as e:
            logger.error(f"Failed to create vector store: {str(e)}")
            raise ChunkingError(f"Failed to create vector store: {str(e)}") 