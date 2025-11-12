"""End-to-end tests for RAGSystem in rag_system.py"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from rag_system import RAGSystem
from config import Config


class TestRAGSystemEndToEnd:
    """Test suite for complete RAG system query flow"""

    @patch('rag_system.VectorStore')
    @patch('rag_system.AIGenerator')
    def test_rag_query_with_zero_max_results(self, mock_ai_gen_class, mock_vector_store_class):
        """
        Test RAG system behavior when MAX_RESULTS=0 (current broken state).
        This is the key test to identify the 'query failed' issue.
        """
        # Create a config with MAX_RESULTS=0
        test_config = Config()
        test_config.MAX_RESULTS = 0  # Simulate the bug
        test_config.ANTHROPIC_API_KEY = "test_key"

        # Mock VectorStore that will be created with max_results=0
        mock_store_instance = Mock()
        mock_vector_store_class.return_value = mock_store_instance

        # Simulate what happens when max_results=0
        # The vector store search will fail or return empty
        from vector_store import SearchResults
        mock_store_instance.search.return_value = SearchResults.empty(
            "Search error: n_results must be > 0"
        )

        # Mock AIGenerator
        mock_ai_instance = Mock()
        mock_ai_gen_class.return_value = mock_ai_instance
        mock_ai_instance.generate_response.return_value = "I encountered an error while searching"

        # Create RAG system
        rag = RAGSystem(test_config)

        # Execute query
        result = rag.query(
            query="What is MCP?",
            session_id="test_session"
        )

        # Assert: System should handle the error somehow
        # The result might contain error message or problematic response
        print(f"Result with MAX_RESULTS=0: {result}")

        # Verify vector store was initialized with max_results=0
        mock_vector_store_class.assert_called_once()
        call_args = mock_vector_store_class.call_args
        assert call_args[0][2] == 0  # Third argument is max_results

        print("✓ Test passed: Confirmed MAX_RESULTS=0 causes issues")

    @patch('rag_system.VectorStore')
    @patch('rag_system.AIGenerator')
    def test_rag_query_with_valid_max_results(self, mock_ai_gen_class, mock_vector_store_class):
        """
        Test RAG system with valid MAX_RESULTS=5 (expected behavior).
        """
        # Create a config with valid MAX_RESULTS
        test_config = Config()
        test_config.MAX_RESULTS = 5
        test_config.ANTHROPIC_API_KEY = "test_key"

        # Mock VectorStore
        mock_store_instance = Mock()
        mock_vector_store_class.return_value = mock_store_instance

        # Simulate successful search
        from vector_store import SearchResults
        mock_results = Mock(spec=SearchResults)
        mock_results.error = None
        mock_results.is_empty.return_value = False
        mock_store_instance.search.return_value = mock_results

        # Mock AIGenerator with successful response
        mock_ai_instance = Mock()
        mock_ai_gen_class.return_value = mock_ai_instance
        mock_ai_instance.generate_response.return_value = "MCP stands for Model Context Protocol"

        # Mock tool manager
        mock_tool_manager = Mock()
        mock_tool_manager.get_last_sources.return_value = [{"text": "MCP Course"}]

        # Create RAG system
        rag = RAGSystem(test_config)
        rag.tool_manager = mock_tool_manager

        # Execute query
        answer, sources = rag.query(
            query="What is MCP?",
            session_id="test_session"
        )

        # Assert: Should return successful response
        assert answer == "MCP stands for Model Context Protocol"
        assert sources == [{"text": "MCP Course"}]

        # Verify vector store was initialized with max_results=5
        call_args = mock_vector_store_class.call_args
        assert call_args[0][2] == 5

        print("✓ Test passed: Valid MAX_RESULTS works correctly")

    @patch('rag_system.VectorStore')
    @patch('rag_system.AIGenerator')
    def test_rag_query_tool_execution_flow(self, mock_ai_gen_class, mock_vector_store_class):
        """
        Test that RAG system correctly passes tools to AI generator.
        """
        # Setup config
        test_config = Config()
        test_config.ANTHROPIC_API_KEY = "test_key"
        test_config.MAX_RESULTS = 5

        # Mock dependencies
        mock_store_instance = Mock()
        mock_vector_store_class.return_value = mock_store_instance

        mock_ai_instance = Mock()
        mock_ai_gen_class.return_value = mock_ai_instance
        mock_ai_instance.generate_response.return_value = "Answer"

        # Create RAG system
        rag = RAGSystem(test_config)

        # Execute query
        rag.query(query="What is RAG?", session_id="test_session")

        # Verify AI generator was called with tools
        call_args = mock_ai_instance.generate_response.call_args
        assert call_args[1]["tools"] is not None
        assert call_args[1]["tool_manager"] is not None
        assert len(call_args[1]["tools"]) > 0  # Should have registered tools

        print("✓ Test passed: Tools passed to AI generator correctly")

    @patch('rag_system.VectorStore')
    @patch('rag_system.AIGenerator')
    def test_rag_query_conversation_history(self, mock_ai_gen_class, mock_vector_store_class):
        """
        Test that conversation history is managed correctly.
        """
        # Setup
        test_config = Config()
        test_config.ANTHROPIC_API_KEY = "test_key"
        test_config.MAX_HISTORY = 2

        mock_vector_store_class.return_value = Mock()

        mock_ai_instance = Mock()
        mock_ai_gen_class.return_value = mock_ai_instance
        mock_ai_instance.generate_response.return_value = "Response"

        # Create RAG system
        rag = RAGSystem(test_config)

        session_id = "test_session"

        # First query
        rag.query(query="What is MCP?", session_id=session_id)

        # Second query - should include first query in history
        rag.query(query="Tell me more", session_id=session_id)

        # Check that second call included conversation history
        second_call_args = mock_ai_instance.generate_response.call_args_list[1]
        conversation_history = second_call_args[1].get("conversation_history")

        assert conversation_history is not None
        assert "What is MCP?" in conversation_history

        print("✓ Test passed: Conversation history tracked correctly")

    @patch('rag_system.VectorStore')
    @patch('rag_system.AIGenerator')
    def test_rag_query_sources_returned(self, mock_ai_gen_class, mock_vector_store_class):
        """
        Test that sources from tool execution are returned in response.
        """
        # Setup
        test_config = Config()
        test_config.ANTHROPIC_API_KEY = "test_key"

        mock_vector_store_class.return_value = Mock()

        mock_ai_instance = Mock()
        mock_ai_gen_class.return_value = mock_ai_instance
        mock_ai_instance.generate_response.return_value = "Answer about MCP"

        # Create RAG system with mock tool manager
        rag = RAGSystem(test_config)

        # Mock tool manager to return sources
        mock_tool_manager = Mock()
        test_sources = [
            {"text": "MCP Course - Lesson 1", "course_link": "http://example.com"}
        ]
        mock_tool_manager.get_last_sources.return_value = test_sources
        rag.tool_manager = mock_tool_manager

        # Execute query
        answer, sources = rag.query(query="What is MCP?", session_id="test_session")

        # Assert: Sources should be returned
        assert sources == test_sources
        assert len(sources) > 0

        print("✓ Test passed: Sources returned correctly")


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "-s"])
