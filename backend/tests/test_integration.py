"""
Integration tests for RAG System
Tests the system with real configuration and dependencies
"""
import pytest
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config import config
from vector_store import VectorStore


class TestConfigurationIntegration:
    """Test that configuration values are set correctly"""

    def test_max_results_is_not_zero(self):
        """
        Critical test: MAX_RESULTS must not be 0
        This prevents the 'list index out of range' bug
        """
        assert config.MAX_RESULTS > 0, (
            f"MAX_RESULTS is {config.MAX_RESULTS}, but must be greater than 0. "
            "Setting MAX_RESULTS to 0 causes search to return empty results."
        )

    def test_max_results_is_reasonable(self):
        """Test that MAX_RESULTS is within a reasonable range"""
        assert 1 <= config.MAX_RESULTS <= 20, (
            f"MAX_RESULTS is {config.MAX_RESULTS}, but should be between 1 and 20. "
            "Too few results may miss relevant content, too many may be overwhelming."
        )

    def test_chunk_size_is_positive(self):
        """Test that chunk size is positive"""
        assert config.CHUNK_SIZE > 0, "CHUNK_SIZE must be positive"

    def test_chunk_overlap_is_valid(self):
        """Test that chunk overlap is less than chunk size"""
        assert config.CHUNK_OVERLAP < config.CHUNK_SIZE, (
            f"CHUNK_OVERLAP ({config.CHUNK_OVERLAP}) must be less than "
            f"CHUNK_SIZE ({config.CHUNK_SIZE})"
        )

    def test_anthropic_api_key_exists(self):
        """Test that API key is configured"""
        assert config.ANTHROPIC_API_KEY, (
            "ANTHROPIC_API_KEY is not set. Please configure it in .env file."
        )


class TestVectorStoreIntegration:
    """Integration tests for VectorStore with real ChromaDB"""

    @pytest.fixture
    def vector_store(self):
        """Create a real VectorStore instance"""
        return VectorStore(
            chroma_path=config.CHROMA_PATH,
            embedding_model=config.EMBEDDING_MODEL,
            max_results=config.MAX_RESULTS
        )

    def test_vector_store_initializes_with_config(self, vector_store):
        """Test that VectorStore can initialize with config values"""
        assert vector_store is not None
        assert vector_store.max_results == config.MAX_RESULTS

    def test_vector_store_max_results_applied(self, vector_store):
        """
        Test that max_results from config is actually used
        This would catch the MAX_RESULTS=0 bug
        """
        assert vector_store.max_results > 0, (
            "VectorStore max_results is 0 or negative, which will cause "
            "search queries to fail"
        )

    def test_vector_store_has_collections(self, vector_store):
        """Test that VectorStore has the required collections"""
        assert hasattr(vector_store, 'course_catalog')
        assert hasattr(vector_store, 'course_content')

    def test_can_query_existing_courses(self, vector_store):
        """Test that we can query the vector store for existing content"""
        try:
            # This should not raise an error even if no results found
            results = vector_store.search(
                query="test query",
                limit=config.MAX_RESULTS
            )
            assert results is not None
            # Results can be empty, but should not cause an error
        except Exception as e:
            pytest.fail(f"Vector store search failed: {e}")


class TestEndToEndIntegration:
    """End-to-end integration tests"""

    def test_search_with_actual_config_values(self):
        """
        Test that search works with actual configuration
        This is the test that would have caught the MAX_RESULTS=0 bug
        """
        # Create VectorStore with real config
        vector_store = VectorStore(
            chroma_path=config.CHROMA_PATH,
            embedding_model=config.EMBEDDING_MODEL,
            max_results=config.MAX_RESULTS
        )

        # Perform a search (this would fail if MAX_RESULTS=0)
        results = vector_store.search(query="MCP")

        # The search should not error out
        # Results might be empty if no data loaded, but structure should be valid
        assert hasattr(results, 'documents')
        assert hasattr(results, 'metadata')
        assert isinstance(results.documents, list)
        assert isinstance(results.metadata, list)

    def test_config_values_work_together(self):
        """Test that all config values are compatible"""
        # Create a VectorStore to test initialization
        try:
            vector_store = VectorStore(
                chroma_path=config.CHROMA_PATH,
                embedding_model=config.EMBEDDING_MODEL,
                max_results=config.MAX_RESULTS
            )
            assert vector_store is not None
        except Exception as e:
            pytest.fail(f"Configuration values are incompatible: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
