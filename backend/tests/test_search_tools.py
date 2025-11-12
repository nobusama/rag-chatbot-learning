"""Tests for CourseSearchTool in search_tools.py"""
import pytest
from unittest.mock import Mock, MagicMock
from search_tools import CourseSearchTool
from vector_store import SearchResults


class TestCourseSearchTool:
    """Test suite for CourseSearchTool.execute() method"""

    def test_execute_with_zero_max_results(self):
        """
        Test CourseSearchTool behavior when VectorStore has max_results=0.
        This should reveal the root cause of 'query failed' error.
        """
        # Create a mock VectorStore
        mock_store = Mock()

        # Simulate what happens when max_results=0:
        # ChromaDB might return empty results or raise an error
        mock_store.search.return_value = SearchResults.empty("Search error: invalid n_results")

        # Create tool with mock store
        tool = CourseSearchTool(mock_store)

        # Execute search
        result = tool.execute(query="What is MCP?")

        # Assert: Should return an error message
        assert "error" in result.lower() or "no relevant content" in result.lower()
        print(f"✓ Test passed: Tool returned: {result}")

    def test_execute_with_valid_configuration(self):
        """
        Test CourseSearchTool with valid max_results configuration.
        This should work correctly.
        """
        # Create mock VectorStore
        mock_store = Mock()

        # Simulate successful search with results
        mock_results = Mock(spec=SearchResults)
        mock_results.error = None
        mock_results.is_empty.return_value = False
        mock_results.documents = ["MCP stands for Model Context Protocol"]
        mock_results.metadata = [{"course_title": "MCP Course", "lesson_number": 1}]

        mock_store.search.return_value = mock_results
        mock_store.get_course_link.return_value = "http://example.com/course"
        mock_store.get_lesson_link.return_value = "http://example.com/lesson/1"

        # Create tool
        tool = CourseSearchTool(mock_store)

        # Execute search
        result = tool.execute(query="What is MCP?")

        # Assert: Should return formatted content
        assert "MCP Course" in result
        assert "Model Context Protocol" in result
        print(f"✓ Test passed: Tool returned formatted results")

    def test_execute_with_empty_results(self):
        """
        Test CourseSearchTool when search returns no results.
        """
        # Create mock VectorStore
        mock_store = Mock()

        # Simulate empty results (not an error, just no matches)
        mock_results = Mock(spec=SearchResults)
        mock_results.error = None
        mock_results.is_empty.return_value = True

        mock_store.search.return_value = mock_results

        # Create tool
        tool = CourseSearchTool(mock_store)

        # Execute search
        result = tool.execute(query="Non-existent topic")

        # Assert: Should return "No relevant content found" message
        assert "no relevant content found" in result.lower()
        print(f"✓ Test passed: Tool returned: {result}")

    def test_execute_with_search_error(self):
        """
        Test CourseSearchTool when VectorStore returns an error.
        """
        # Create mock VectorStore
        mock_store = Mock()

        # Simulate search error
        mock_results = Mock(spec=SearchResults)
        mock_results.error = "Database connection failed"

        mock_store.search.return_value = mock_results

        # Create tool
        tool = CourseSearchTool(mock_store)

        # Execute search
        result = tool.execute(query="What is MCP?")

        # Assert: Should return the error message
        assert result == "Database connection failed"
        print(f"✓ Test passed: Tool correctly returned error")

    def test_execute_with_course_filter(self):
        """
        Test CourseSearchTool with course_name filter parameter.
        """
        # Create mock VectorStore
        mock_store = Mock()

        # Simulate search with course filter
        mock_results = Mock(spec=SearchResults)
        mock_results.error = None
        mock_results.is_empty.return_value = False
        mock_results.documents = ["Lesson content"]
        mock_results.metadata = [{"course_title": "MCP Course", "lesson_number": 2}]

        mock_store.search.return_value = mock_results
        mock_store.get_course_link.return_value = "http://example.com/course"
        mock_store.get_lesson_link.return_value = "http://example.com/lesson/2"

        # Create tool
        tool = CourseSearchTool(mock_store)

        # Execute search with course filter
        result = tool.execute(query="lesson content", course_name="MCP")

        # Verify VectorStore.search was called with correct parameters
        mock_store.search.assert_called_once_with(
            query="lesson content",
            course_name="MCP",
            lesson_number=None
        )

        assert "MCP Course" in result
        print(f"✓ Test passed: Course filter applied correctly")


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "-s"])
