"""
Tests for the key point extractor module.
"""

import os
import unittest
from unittest.mock import patch, MagicMock

# Add src to path
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))

from analysis.key_point_extractor import KeyPointExtractor
from utils.error_handler import AnalysisError


class TestKeyPointExtractor(unittest.TestCase):
    """Tests for the KeyPointExtractor class."""
    
    def setUp(self):
        """Set up test environment."""
        # Create a mock vector store
        self.mock_vector_store = MagicMock()
        
        # Mock the similarity_search method
        self.mock_vector_store.similarity_search = MagicMock()
        
        # Create mock documents
        self.mock_doc1 = MagicMock()
        self.mock_doc1.page_content = "This is a test document 1 with deadline information: 31st December 2023."
        
        self.mock_doc2 = MagicMock()
        self.mock_doc2.page_content = "This is a test document 2 with project requirements: build a system."
        
        # Set return value for similarity_search
        self.mock_vector_store.similarity_search.return_value = [self.mock_doc1, self.mock_doc2]
        
        # Create the extractor with the mock vector store
        with patch("analysis.key_point_extractor.Ollama"):
            self.extractor = KeyPointExtractor(self.mock_vector_store)
    
    @patch("analysis.key_point_extractor.Ollama")
    def test_init_llm(self, mock_ollama):
        """Test LLM initialization."""
        # Arrange
        mock_ollama_instance = MagicMock()
        mock_ollama.return_value = mock_ollama_instance
        
        # Act
        extractor = KeyPointExtractor(self.mock_vector_store)
        
        # Assert
        self.assertEqual(extractor.vector_store, self.mock_vector_store)
        self.assertIsNotNone(extractor.llm)
        mock_ollama.assert_called_once()
    
    def test_create_search_query(self):
        """Test search query creation."""
        # Act
        deadline_query = self.extractor._create_search_query("Deadline")
        cost_query = self.extractor._create_search_query("Cost")
        custom_query = self.extractor._create_search_query("Custom Point")
        
        # Assert
        self.assertIn("deadline", deadline_query.lower())
        self.assertIn("submission", deadline_query.lower())
        self.assertIn("cost", cost_query.lower())
        self.assertIn("budget", cost_query.lower())
        self.assertIn("custom point", custom_query.lower())
    
    def test_retrieve_relevant_chunks(self):
        """Test retrieving relevant chunks."""
        # Arrange
        query = "test query"
        
        # Act
        result = self.extractor._retrieve_relevant_chunks(query)
        
        # Assert
        self.mock_vector_store.similarity_search.assert_called_once_with(query, k=5)
        self.assertIn(self.mock_doc1.page_content, result)
        self.assertIn(self.mock_doc2.page_content, result)
    
    @patch("analysis.key_point_extractor.LLMChain")
    def test_process_with_llm(self, mock_llm_chain):
        """Test processing with LLM."""
        # Arrange
        mock_chain = MagicMock()
        mock_chain.run.return_value = "Extracted key point information"
        mock_llm_chain.return_value = mock_chain
        
        key_point = "Deadline"
        context = "Sample context"
        
        # Act
        result = self.extractor._process_with_llm(key_point, context)
        
        # Assert
        self.assertEqual(result, "Extracted key point information")
        mock_chain.run.assert_called_once_with(context=context)
    
    @patch.object(KeyPointExtractor, "_extract_single_point")
    def test_extract_key_points(self, mock_extract_single):
        """Test extracting all key points."""
        # Arrange
        mock_extract_single.side_effect = [
            "Deadline info",
            "Project requirements info",
            "Cost info",
            "Quality checking info"
        ]
        
        # Act
        result = self.extractor.extract_key_points()
        
        # Assert
        self.assertEqual(len(result), 4)
        self.assertEqual(result["Deadline"], "Deadline info")
        self.assertEqual(result["Project Requirement"], "Project requirements info")
        self.assertEqual(result["Cost"], "Cost info")
        self.assertEqual(result["Quality Checking"], "Quality checking info")
        self.assertEqual(mock_extract_single.call_count, 4)
    
    @patch.object(KeyPointExtractor, "_create_search_query")
    @patch.object(KeyPointExtractor, "_retrieve_relevant_chunks")
    @patch.object(KeyPointExtractor, "_process_with_llm")
    def test_extract_single_point(self, mock_process, mock_retrieve, mock_create_query):
        """Test extracting a single key point."""
        # Arrange
        mock_create_query.return_value = "test query"
        mock_retrieve.return_value = "test context"
        mock_process.return_value = "extracted information"
        
        # Act
        result = self.extractor._extract_single_point("Deadline")
        
        # Assert
        self.assertEqual(result, "extracted information")
        mock_create_query.assert_called_once_with("Deadline")
        mock_retrieve.assert_called_once_with("test query")
        mock_process.assert_called_once_with("Deadline", "test context")
    
    def test_create_prompt_template(self):
        """Test prompt template creation."""
        # Act
        deadline_prompt = self.extractor._create_prompt_template("Deadline")
        cost_prompt = self.extractor._create_prompt_template("Cost")
        custom_prompt = self.extractor._create_prompt_template("Custom Point")
        
        # Assert
        self.assertIn("Deadline", deadline_prompt.partial_variables["key_point"])
        self.assertIn("Cost", cost_prompt.partial_variables["key_point"])
        self.assertIn("Custom Point", custom_prompt.partial_variables["key_point"])
        
        # Check that the deadline prompt has specific instructions
        self.assertIn("Submission deadline", deadline_prompt.partial_variables["specific_instructions"])


if __name__ == "__main__":
    unittest.main() 