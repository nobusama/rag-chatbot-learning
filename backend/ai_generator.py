import anthropic
from typing import List, Optional, Dict, Any

class AIGenerator:
    """Handles interactions with Anthropic's Claude API for generating responses"""

    # Configuration constants
    DEFAULT_TEMPERATURE = 0
    DEFAULT_MAX_TOKENS = 800

    # Static system prompt to avoid rebuilding on each call
    SYSTEM_PROMPT = """ You are an AI assistant specialized in course materials and educational content with access to a comprehensive search tool for course information.

Search Tool Usage:
- Use the search tool **only** for questions about specific course content or detailed educational materials
- **You can use the search tool multiple times if needed** to answer complex queries
- Use tools iteratively for multi-step reasoning (e.g., comparing courses, gathering detailed information)
- Synthesize search results into accurate, fact-based responses
- If search yields no results, state this clearly without offering alternatives

Response Protocol:
- **General knowledge questions**: Answer using existing knowledge without searching
- **Course-specific questions**: Search first, then answer
- **Complex questions**: Use multiple searches to gather all necessary information
- **No meta-commentary**:
 - Provide direct answers only — no reasoning process, search explanations, or question-type analysis
 - Do not mention "based on the search results"


All responses must be:
1. **Brief, Concise and focused** - Get to the point quickly
2. **Educational** - Maintain instructional value
3. **Clear** - Use accessible language
4. **Example-supported** - Include relevant examples when they aid understanding
Provide only the direct answer to what was asked.
"""

    def __init__(self, api_key: str, model: str):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model

        # Pre-build base API parameters
        self.base_params = {
            "model": self.model,
            "temperature": self.DEFAULT_TEMPERATURE,
            "max_tokens": self.DEFAULT_MAX_TOKENS
        }

    def generate_response(self, query: str,
                         conversation_history: Optional[str] = None,
                         tools: Optional[List] = None,
                         tool_manager=None,
                         max_rounds: int = 5) -> str:
        """
        Generate AI response with optional tool usage and conversation context.

        Args:
            query: The user's question or request
            conversation_history: Previous messages for context
            tools: Available tools the AI can use
            tool_manager: Manager to execute tools
            max_rounds: Maximum number of tool execution rounds (default: 5)

        Returns:
            Generated response as string
        """

        # Build system content efficiently
        system_content = self._build_system_content(conversation_history)

        # Prepare API call parameters
        api_params = self._prepare_api_params(query, system_content, tools)

        # Get response from Claude
        response = self.client.messages.create(**api_params)

        # Handle tool execution if needed
        if response.stop_reason == "tool_use" and tool_manager:
            return self._handle_tool_execution(response, api_params, tool_manager, max_rounds)

        # Return direct response
        return response.content[0].text

    def _build_system_content(self, conversation_history: Optional[str]) -> str:
        """Build system prompt with optional conversation history"""
        if conversation_history:
            return f"{self.SYSTEM_PROMPT}\n\nPrevious conversation:\n{conversation_history}"
        return self.SYSTEM_PROMPT

    def _prepare_api_params(self, query: str, system_content: str, tools: Optional[List]) -> Dict[str, Any]:
        """Prepare parameters for API call"""
        api_params = {
            **self.base_params,
            "messages": [{"role": "user", "content": query}],
            "system": system_content
        }

        # Add tools if available
        if tools:
            api_params["tools"] = tools
            api_params["tool_choice"] = {"type": "auto"}

        return api_params

    def _handle_tool_execution(self, initial_response, base_params: Dict[str, Any], tool_manager, max_rounds: int = 5):
        """
        Handle execution of tool calls across multiple rounds.

        This method implements iterative tool execution, allowing Claude to use
        multiple tools across separate rounds for complex multi-step queries.

        Args:
            initial_response: The response containing tool use requests
            base_params: Base API parameters
            tool_manager: Manager to execute tools
            max_rounds: Maximum number of tool execution rounds

        Returns:
            Final response text after tool execution
        """
        # Start with initial messages
        messages = base_params["messages"].copy()
        current_response = initial_response
        round_count = 0

        # Iteratively handle tool use across multiple rounds
        while round_count < max_rounds:
            # Build messages with current tool results
            messages = self._build_messages_with_tools(
                messages,
                current_response,
                tool_manager
            )

            # Get next response from Claude
            # Include tools parameter if available
            tools = base_params.get("tools")
            next_response = self._get_final_response(messages, base_params["system"], tools)

            # Check if Claude wants to use more tools
            if next_response.stop_reason == "tool_use":
                # Continue to next round
                current_response = next_response
                round_count += 1
            else:
                # Claude finished - return final answer
                return next_response.content[0].text

        # Max rounds reached - return last response text
        return next_response.content[0].text

    def _build_messages_with_tools(self, initial_messages: List[Dict], response, tool_manager) -> List[Dict]:
        """
        Build message history including tool execution results.

        Args:
            initial_messages: Original user messages
            response: AI response with tool use requests
            tool_manager: Manager to execute tools

        Returns:
            Complete message history with tool results
        """
        messages = initial_messages.copy()

        # Add AI's tool use response
        messages.append({"role": "assistant", "content": response.content})

        # Execute tools and collect results
        tool_results = self._execute_tools(response.content, tool_manager)

        # Add tool results as user message
        if tool_results:
            messages.append({"role": "user", "content": tool_results})

        return messages

    def _execute_tools(self, content_blocks, tool_manager) -> List[Dict]:
        """
        Execute all tool calls from the response.

        Args:
            content_blocks: Content blocks from AI response
            tool_manager: Manager to execute tools

        Returns:
            List of tool results
        """
        tool_results = []

        for content_block in content_blocks:
            if content_block.type == "tool_use":
                tool_result = tool_manager.execute_tool(
                    content_block.name,
                    **content_block.input
                )

                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": content_block.id,
                    "content": tool_result
                })

        return tool_results

    def _get_final_response(self, messages: List[Dict], system_content: str, tools: Optional[List] = None):
        """
        Get final response after tool execution.

        Args:
            messages: Complete message history
            system_content: System prompt
            tools: Available tools for the AI

        Returns:
            Final AI response
        """
        final_params = {
            **self.base_params,
            "messages": messages,
            "system": system_content
        }

        # Add tools if available
        if tools:
            final_params["tools"] = tools
            final_params["tool_choice"] = {"type": "auto"}

        return self.client.messages.create(**final_params)
