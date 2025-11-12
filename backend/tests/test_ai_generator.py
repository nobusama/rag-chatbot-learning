"""Tests for AIGenerator tool calling mechanism in ai_generator.py"""
import pytest
from unittest.mock import Mock, MagicMock, patch
from ai_generator import AIGenerator


class TestAIGeneratorToolCalling:
    """Test suite for AIGenerator's tool calling functionality"""

    def test_generate_response_without_tools(self):
        """
        Test AIGenerator can generate direct responses without tool usage.
        """
        # Mock Anthropic client
        mock_client = Mock()
        mock_response = Mock()
        mock_response.stop_reason = "end_turn"
        mock_response.content = [Mock(text="This is a direct answer")]
        mock_client.messages.create.return_value = mock_response

        # Create generator with mock client
        generator = AIGenerator(api_key="test_key", model="claude-3-sonnet")
        generator.client = mock_client

        # Generate response without tools
        result = generator.generate_response(query="Hello")

        # Assert: Should return direct text response
        assert result == "This is a direct answer"
        print("✓ Test passed: Direct response works")

    def test_generate_response_with_tool_use(self):
        """
        Test AIGenerator correctly handles tool_use stop_reason and executes tools.
        """
        # Mock Anthropic client
        mock_client = Mock()

        # First response: AI wants to use a tool
        mock_tool_block = Mock()
        mock_tool_block.type = "tool_use"
        mock_tool_block.name = "search_course_content"
        mock_tool_block.id = "tool_123"
        mock_tool_block.input = {"query": "What is MCP?"}

        mock_initial_response = Mock()
        mock_initial_response.stop_reason = "tool_use"
        mock_initial_response.content = [mock_tool_block]

        # Second response: AI's final answer after tool execution
        mock_final_response = Mock()
        mock_final_response.content = [Mock(text="Based on the search, MCP is...")]

        # Configure mock to return different responses
        mock_client.messages.create.side_effect = [mock_initial_response, mock_final_response]

        # Mock tool manager
        mock_tool_manager = Mock()
        mock_tool_manager.execute_tool.return_value = "MCP stands for Model Context Protocol"

        # Create generator
        generator = AIGenerator(api_key="test_key", model="claude-3-sonnet")
        generator.client = mock_client

        # Generate response with tools
        tools = [{"name": "search_course_content", "description": "Search courses"}]
        result = generator.generate_response(
            query="What is MCP?",
            tools=tools,
            tool_manager=mock_tool_manager
        )

        # Assert: Tool should be executed and final response returned
        mock_tool_manager.execute_tool.assert_called_once_with(
            "search_course_content",
            query="What is MCP?"
        )
        assert result == "Based on the search, MCP is..."
        print("✓ Test passed: Tool execution flow works")

    def test_tool_error_propagation(self):
        """
        Test what happens when tool execution returns an error message.
        This simulates the 'query failed' scenario.
        """
        # Mock Anthropic client
        mock_client = Mock()

        # First response: AI wants to use a tool
        mock_tool_block = Mock()
        mock_tool_block.type = "tool_use"
        mock_tool_block.name = "search_course_content"
        mock_tool_block.id = "tool_123"
        mock_tool_block.input = {"query": "What is MCP?"}

        mock_initial_response = Mock()
        mock_initial_response.stop_reason = "tool_use"
        mock_initial_response.content = [mock_tool_block]

        # Second response: AI receives error from tool
        mock_final_response = Mock()
        mock_final_response.content = [Mock(text="I encountered an error searching")]

        mock_client.messages.create.side_effect = [mock_initial_response, mock_final_response]

        # Mock tool manager that returns an error
        mock_tool_manager = Mock()
        mock_tool_manager.execute_tool.return_value = "Search error: invalid n_results"

        # Create generator
        generator = AIGenerator(api_key="test_key", model="claude-3-sonnet")
        generator.client = mock_client

        # Generate response
        tools = [{"name": "search_course_content", "description": "Search courses"}]
        result = generator.generate_response(
            query="What is MCP?",
            tools=tools,
            tool_manager=mock_tool_manager
        )

        # Assert: Error should propagate to final response
        # AI should handle the error gracefully
        assert result == "I encountered an error searching"
        print(f"✓ Test passed: Tool error propagated, AI response: {result}")

    def test_handle_tool_execution_message_building(self):
        """
        Test that _handle_tool_execution correctly builds message history.
        """
        # Mock Anthropic client
        mock_client = Mock()

        # Tool use response
        mock_tool_block = Mock()
        mock_tool_block.type = "tool_use"
        mock_tool_block.name = "get_course_outline"
        mock_tool_block.id = "tool_456"
        mock_tool_block.input = {"course_name": "MCP"}

        mock_initial_response = Mock()
        mock_initial_response.stop_reason = "tool_use"
        mock_initial_response.content = [mock_tool_block]

        # Final response
        mock_final_response = Mock()
        mock_final_response.content = [Mock(text="Here is the course outline")]

        mock_client.messages.create.side_effect = [mock_initial_response, mock_final_response]

        # Mock tool manager
        mock_tool_manager = Mock()
        mock_tool_manager.execute_tool.return_value = "Course: MCP\nLesson 1: Introduction"

        # Create generator
        generator = AIGenerator(api_key="test_key", model="claude-3-sonnet")
        generator.client = mock_client

        # Generate response
        tools = [{"name": "get_course_outline", "description": "Get outline"}]
        result = generator.generate_response(
            query="Show MCP course outline",
            tools=tools,
            tool_manager=mock_tool_manager
        )

        # Check that messages were built correctly
        # Second call should include tool results
        second_call_args = mock_client.messages.create.call_args_list[1]
        messages = second_call_args[1]["messages"]

        # Should have 3 messages: user query, assistant tool use, user tool result
        assert len(messages) == 3
        assert messages[0]["role"] == "user"
        assert messages[1]["role"] == "assistant"
        assert messages[2]["role"] == "user"
        assert "tool_result" in str(messages[2]["content"])

        print("✓ Test passed: Message history built correctly")

    def test_conversation_history_included(self):
        """
        Test that conversation history is included in system prompt.
        """
        # Mock Anthropic client
        mock_client = Mock()
        mock_response = Mock()
        mock_response.stop_reason = "end_turn"
        mock_response.content = [Mock(text="Response with context")]
        mock_client.messages.create.return_value = mock_response

        # Create generator
        generator = AIGenerator(api_key="test_key", model="claude-3-sonnet")
        generator.client = mock_client

        # Generate response with conversation history
        conversation_history = "User: What is RAG?\nAssistant: RAG is Retrieval-Augmented Generation"
        result = generator.generate_response(
            query="Tell me more",
            conversation_history=conversation_history
        )

        # Check that system prompt included conversation history
        call_args = mock_client.messages.create.call_args
        system_content = call_args[1]["system"]

        assert "Previous conversation" in system_content
        assert "What is RAG?" in system_content
        print("✓ Test passed: Conversation history included in system prompt")


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "-s"])
