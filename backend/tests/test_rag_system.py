"""
Test suite for RAG System components
Tests: Course search, query responses, and session management
"""
import pytest
from unittest.mock import Mock, MagicMock, patch
import sys
import os

# Add parent directory to path to import modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from rag_system import RAGSystem
from config import Config
from session_manager import SessionManager
from search_tools import CourseSearchTool, ToolManager
from vector_store import SearchResults


class TestCourseSearch:
    """Test suite for course search functionality"""

    @pytest.fixture
    def mock_config(self):
        """Create a mock configuration"""
        config = Config()
        config.ANTHROPIC_API_KEY = "test-key"
        config.MAX_RESULTS = 5
        config.MAX_HISTORY = 2
        return config

    @pytest.fixture
    def mock_vector_store(self):
        """Create a mock vector store"""
        store = Mock()
        # Mock successful search results
        store.search.return_value = SearchResults(
            documents=["Test content about MCP course"],
            metadata=[{
                'course_title': 'Introduction to MCP',
                'lesson_number': 1
            }],
            distances=[0.1],
            error=None
        )
        store.get_lesson_link.return_value = "https://example.com/lesson1"
        return store

    @pytest.fixture
    def search_tool(self, mock_vector_store):
        """Create a CourseSearchTool with mock vector store"""
        return CourseSearchTool(mock_vector_store)

    def test_search_tool_executes_successfully(self, search_tool):
        """Test that search tool can execute a basic search"""
        result = search_tool.execute(query="What is MCP?")

        assert result is not None
        assert isinstance(result, str)
        assert len(result) > 0
        assert "MCP" in result or "Introduction" in result

    def test_search_tool_with_course_filter(self, search_tool):
        """Test search with course name filter"""
        result = search_tool.execute(
            query="What is covered?",
            course_name="Introduction to MCP"
        )

        assert result is not None
        assert isinstance(result, str)

    def test_search_tool_with_lesson_filter(self, search_tool):
        """Test search with lesson number filter"""
        result = search_tool.execute(
            query="What is covered?",
            lesson_number=1
        )

        assert result is not None
        assert isinstance(result, str)

    def test_search_tool_handles_empty_results(self, mock_vector_store):
        """Test search tool handles empty results gracefully"""
        # Mock empty results
        mock_vector_store.search.return_value = SearchResults(
            documents=[],
            metadata=[],
            distances=[],
            error=None
        )

        search_tool = CourseSearchTool(mock_vector_store)
        result = search_tool.execute(query="nonexistent content")

        assert "No relevant content found" in result

    def test_search_tool_tracks_sources(self, search_tool):
        """Test that search tool tracks sources from searches"""
        # Execute a search
        search_tool.execute(query="What is MCP?")

        # Check that sources were tracked
        assert hasattr(search_tool, 'last_sources')
        assert isinstance(search_tool.last_sources, list)

        # If results were found, sources should be populated
        if search_tool.last_sources:
            source = search_tool.last_sources[0]
            assert 'text' in source


class TestQueryResponse:
    """Test suite for query response functionality"""

    @pytest.fixture
    def mock_config(self):
        """Create a mock configuration"""
        config = Config()
        config.ANTHROPIC_API_KEY = "test-key"
        config.MAX_RESULTS = 5
        config.MAX_HISTORY = 2
        return config

    @pytest.fixture
    def mock_rag_system(self, mock_config):
        """Create a RAG system with mocked dependencies"""
        with patch('rag_system.DocumentProcessor'), \
             patch('rag_system.VectorStore'), \
             patch('rag_system.AIGenerator'), \
             patch('rag_system.SessionManager'), \
             patch('rag_system.ToolManager'):

            rag = RAGSystem(mock_config)

            # Mock the AI generator response
            rag.ai_generator.generate_response = Mock(
                return_value="MCP stands for Model Context Protocol, a standardized way for AI assistants to access external tools and data."
            )

            # Mock the tool manager to return empty sources
            rag.tool_manager.get_last_sources = Mock(return_value=[
                {"text": "Introduction to MCP - Lesson 1", "url": "https://example.com/lesson1"}
            ])
            rag.tool_manager.reset_sources = Mock()

            return rag

    def test_query_returns_string_response(self, mock_rag_system):
        """Test that query returns a string response"""
        response, sources = mock_rag_system.query("What is MCP?")

        assert isinstance(response, str)
        assert len(response) > 0

    def test_query_returns_sources(self, mock_rag_system):
        """Test that query returns sources along with response"""
        response, sources = mock_rag_system.query("What is MCP?")

        assert isinstance(sources, list)
        # Sources might be empty if no search was performed
        if sources:
            assert 'text' in sources[0]

    def test_query_with_session_id(self, mock_rag_system):
        """Test that query works with session ID for context"""
        session_id = "test_session_123"
        response, sources = mock_rag_system.query(
            "What is MCP?",
            session_id=session_id
        )

        assert response is not None
        assert isinstance(response, str)

    def test_query_handles_empty_input(self, mock_rag_system):
        """Test query handles empty string input"""
        # The system should still process empty queries
        response, sources = mock_rag_system.query("")

        assert response is not None
        assert isinstance(response, str)


class TestSessionManagement:
    """Test suite for session management functionality"""

    @pytest.fixture
    def session_manager(self):
        """Create a session manager with max_history=2"""
        return SessionManager(max_history=2)

    def test_create_session(self, session_manager):
        """Test that new sessions can be created"""
        session_id = session_manager.create_session()

        assert session_id is not None
        assert isinstance(session_id, str)
        assert session_id.startswith("session_")

    def test_add_exchange(self, session_manager):
        """Test adding a question-answer exchange"""
        session_id = session_manager.create_session()

        session_manager.add_exchange(
            session_id,
            "What is MCP?",
            "MCP is Model Context Protocol."
        )

        history = session_manager.get_conversation_history(session_id)

        assert history is not None
        assert "What is MCP?" in history
        assert "MCP is Model Context Protocol." in history

    def test_conversation_history_format(self, session_manager):
        """Test that conversation history is properly formatted"""
        session_id = session_manager.create_session()

        session_manager.add_exchange(
            session_id,
            "First question",
            "First answer"
        )

        history = session_manager.get_conversation_history(session_id)

        assert history is not None
        assert "User:" in history or "user" in history.lower()
        assert "Assistant:" in history or "assistant" in history.lower()

    def test_history_limit_enforcement(self, session_manager):
        """Test that history is limited to max_history exchanges"""
        session_id = session_manager.create_session()

        # Add more exchanges than max_history
        for i in range(5):
            session_manager.add_exchange(
                session_id,
                f"Question {i}",
                f"Answer {i}"
            )

        history = session_manager.get_conversation_history(session_id)

        # Should only contain the last 2 exchanges (4 messages total)
        # The oldest exchanges should be removed
        assert history is not None
        assert "Question 0" not in history  # Oldest should be removed
        assert "Question 4" in history      # Newest should be present

    def test_get_history_for_nonexistent_session(self, session_manager):
        """Test getting history for a session that doesn't exist"""
        history = session_manager.get_conversation_history("nonexistent_session")

        assert history is None

    def test_clear_session(self, session_manager):
        """Test clearing a session's history"""
        session_id = session_manager.create_session()

        # Add some exchanges
        session_manager.add_exchange(session_id, "Question", "Answer")

        # Clear the session
        session_manager.clear_session(session_id)

        # History should now be empty
        history = session_manager.get_conversation_history(session_id)
        assert history is None or len(history) == 0


class TestToolManager:
    """Test suite for tool manager functionality"""

    @pytest.fixture
    def tool_manager(self):
        """Create a tool manager"""
        return ToolManager()

    @pytest.fixture
    def mock_search_tool(self):
        """Create a mock search tool"""
        tool = Mock()
        tool.get_tool_definition.return_value = {
            "name": "search_course_content",
            "description": "Search course materials",
            "input_schema": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"}
                }
            }
        }
        tool.execute.return_value = "Search results here"
        tool.last_sources = [{"text": "Test source"}]
        return tool

    def test_register_tool(self, tool_manager, mock_search_tool):
        """Test registering a tool"""
        tool_manager.register_tool(mock_search_tool)

        definitions = tool_manager.get_tool_definitions()
        assert len(definitions) > 0
        assert definitions[0]["name"] == "search_course_content"

    def test_execute_tool(self, tool_manager, mock_search_tool):
        """Test executing a registered tool"""
        tool_manager.register_tool(mock_search_tool)

        result = tool_manager.execute_tool("search_course_content", query="test")

        assert result is not None
        assert isinstance(result, str)

    def test_get_last_sources(self, tool_manager, mock_search_tool):
        """Test retrieving sources from last search"""
        tool_manager.register_tool(mock_search_tool)

        sources = tool_manager.get_last_sources()

        assert isinstance(sources, list)
        if sources:
            assert 'text' in sources[0]

    def test_reset_sources(self, tool_manager, mock_search_tool):
        """Test resetting sources"""
        tool_manager.register_tool(mock_search_tool)

        # Reset sources
        tool_manager.reset_sources()

        # Sources should be empty now
        assert mock_search_tool.last_sources == []


class TestMultiToolExecution:
    """Test suite for multi-tool execution across multiple rounds"""

    @pytest.fixture
    def mock_ai_generator(self):
        """Create a mock AI generator that simulates multi-round tool usage"""
        from ai_generator import AIGenerator

        with patch.object(AIGenerator, '__init__', lambda x, y, z: None):
            generator = AIGenerator(None, None)
            generator.client = Mock()
            generator.base_params = {
                "model": "test-model",
                "temperature": 0,
                "max_tokens": 800
            }

            # Create mock responses for multi-round scenario
            # Round 1: Tool use
            round1_response = Mock()
            round1_response.stop_reason = "tool_use"
            round1_response.content = [
                Mock(type="text", text=""),
                Mock(type="tool_use", id="tool_1", name="search_course_content",
                     input={"query": "Lesson 5"})
            ]

            # Round 2: Another tool use
            round2_response = Mock()
            round2_response.stop_reason = "tool_use"
            round2_response.content = [
                Mock(type="text", text="Based on the search..."),
                Mock(type="tool_use", id="tool_2", name="search_course_content",
                     input={"query": "other courses"})
            ]

            # Round 3: Final answer (no more tools)
            round3_response = Mock()
            round3_response.stop_reason = "end_turn"
            round3_response.content = [
                Mock(type="text", text="Final answer after multiple searches")
            ]

            # Set up the mock to return different responses on successive calls
            generator.client.messages.create = Mock(
                side_effect=[round1_response, round2_response, round3_response]
            )

            return generator

    @pytest.fixture
    def mock_tool_manager(self):
        """Create a mock tool manager"""
        manager = Mock()
        manager.execute_tool = Mock(return_value="Search result")
        return manager

    def test_single_tool_call_backward_compatibility(self, mock_ai_generator, mock_tool_manager):
        """Test that single tool calls still work (backward compatibility)"""
        from ai_generator import AIGenerator

        # Simulate single tool use
        single_response = Mock()
        single_response.stop_reason = "tool_use"
        single_response.content = [
            Mock(type="tool_use", id="tool_1", name="search_course_content",
                 input={"query": "test"})
        ]

        final_response = Mock()
        final_response.stop_reason = "end_turn"
        final_response.content = [Mock(type="text", text="Single tool answer")]

        mock_ai_generator.client.messages.create = Mock(
            side_effect=[single_response, final_response]
        )

        result = mock_ai_generator.generate_response(
            query="What is MCP?",
            tools=[{"name": "search_course_content"}],
            tool_manager=mock_tool_manager,
            max_rounds=5
        )

        assert result == "Single tool answer"
        assert mock_ai_generator.client.messages.create.call_count == 2  # Initial + 1 round

    def test_multiple_tool_calls_across_rounds(self, mock_ai_generator, mock_tool_manager):
        """Test that multiple tool calls across rounds work correctly"""
        result = mock_ai_generator.generate_response(
            query="Are there other courses covering the same topic as Lesson 5?",
            tools=[{"name": "search_course_content"}],
            tool_manager=mock_tool_manager,
            max_rounds=5
        )

        assert result == "Final answer after multiple searches"
        # Should be called 3 times in _handle_tool_execution: round1 + round2 + round3
        # (initial call happens in generate_response before entering _handle_tool_execution)
        assert mock_ai_generator.client.messages.create.call_count == 3

        # Tool manager should be called twice (once per tool_use)
        assert mock_tool_manager.execute_tool.call_count == 2

    def test_max_rounds_limit_enforcement(self, mock_tool_manager):
        """Test that max_rounds limit prevents infinite loops"""
        from ai_generator import AIGenerator

        with patch.object(AIGenerator, '__init__', lambda x, y, z: None):
            generator = AIGenerator(None, None)
            generator.client = Mock()
            generator.base_params = {
                "model": "test-model",
                "temperature": 0,
                "max_tokens": 800
            }

            # Create responses that always want more tools
            tool_response = Mock()
            tool_response.stop_reason = "tool_use"
            tool_response.content = [
                Mock(type="tool_use", id="tool_x", name="search_course_content",
                     input={"query": "test"})
            ]

            # Set up mock to always return tool_use (would loop forever without limit)
            generator.client.messages.create = Mock(return_value=tool_response)

            # Call with max_rounds=3
            result = generator.generate_response(
                query="Test query",
                tools=[{"name": "search_course_content"}],
                tool_manager=mock_tool_manager,
                max_rounds=3
            )

            # Should stop at max_rounds (3 rounds + initial call = 4 total)
            assert generator.client.messages.create.call_count == 4

    def test_no_tools_general_knowledge_question(self):
        """Test that general knowledge questions don't use tools"""
        from ai_generator import AIGenerator

        with patch.object(AIGenerator, '__init__', lambda x, y, z: None):
            generator = AIGenerator(None, None)
            generator.client = Mock()
            generator.base_params = {
                "model": "test-model",
                "temperature": 0,
                "max_tokens": 800
            }

            # Response without tool use
            response = Mock()
            response.stop_reason = "end_turn"
            response.content = [Mock(type="text", text="General knowledge answer")]

            generator.client.messages.create = Mock(return_value=response)

            result = generator.generate_response(
                query="What is Python?",
                tools=[{"name": "search_course_content"}],
                tool_manager=None,
                max_rounds=5
            )

            assert result == "General knowledge answer"
            # Only initial call, no tool rounds
            assert generator.client.messages.create.call_count == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
