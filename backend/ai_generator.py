import anthropic
from typing import List, Optional, Dict, Any

class AIGenerator:
    """Handles interactions with Anthropic's Claude API for generating responses"""
    
    # Static system prompt to avoid rebuilding on each call
    SYSTEM_PROMPT = """ You are an AI assistant specialized in course materials and educational content with access to search tools for course information.

Available Tools:

1. **Course Content Search** (search_course_content):
   - Use when: User asks about specific topics, concepts, or details within course materials
   - Example questions: "How does X work?", "What are the steps for Y?", "Explain Z concept"
   - Returns: Relevant content excerpts from course materials

2. **Course Outline** (get_course_outline):
   - Use when: User wants to see the structure, lesson list, or overview of a course
   - Example questions: "What lessons are in the MCP course?", "Show me the course structure", "List all topics in X course"
   - Returns: Complete course structure with lesson titles and links

Tool Usage Guidelines:
- **Up to 2 sequential tool calls allowed** - Use additional calls to refine or compare results
- Select the appropriate tool based on the question type
- Synthesize tool results into accurate, fact-based responses
- If a tool yields no results, state this clearly without offering alternatives

Response Protocol:
- **General knowledge questions**: Answer using existing knowledge without searching
- **Course-specific questions**: Search first, then answer
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
            "temperature": 0,
            "max_tokens": 800
        }
    
    def generate_response(self, query: str,
                         conversation_history: Optional[str] = None,
                         tools: Optional[List] = None,
                         tool_manager=None) -> str:
        """
        Generate AI response with optional tool usage and conversation context.
        
        Args:
            query: The user's question or request
            conversation_history: Previous messages for context
            tools: Available tools the AI can use
            tool_manager: Manager to execute tools
            
        Returns:
            Generated response as string
        """
        
        # Build system content efficiently - avoid string ops when possible
        system_content = (
            f"{self.SYSTEM_PROMPT}\n\nPrevious conversation:\n{conversation_history}"
            if conversation_history 
            else self.SYSTEM_PROMPT
        )
        
        # Prepare API call parameters efficiently
        api_params = {
            **self.base_params,
            "messages": [{"role": "user", "content": query}],
            "system": system_content
        }
        
        # Add tools if available
        if tools:
            api_params["tools"] = tools
            api_params["tool_choice"] = {"type": "auto"}
        
        # Get response from Claude
        response = self.client.messages.create(**api_params)
        
        # Handle tool execution if needed
        if response.stop_reason == "tool_use" and tool_manager:
            return self._handle_tool_execution(response, api_params, tool_manager)
        
        # Return direct response
        return response.content[0].text
    
    def _handle_tool_execution(self, initial_response, base_params: Dict[str, Any], tool_manager):
        """
        Handle execution of tool calls with support for up to 2 sequential rounds.

        Each round can result in tool calls, and Claude can see previous tool results
        to make informed decisions about whether to call additional tools.

        Args:
            initial_response: The response containing initial tool use requests
            base_params: Base API parameters including tools
            tool_manager: Manager to execute tools

        Returns:
            Final response text after tool execution (up to 2 rounds)
        """
        MAX_ROUNDS = 2

        # Start with existing messages
        messages = base_params["messages"].copy()

        # Track current response (starts with initial tool use response)
        current_response = initial_response
        current_round = 1

        while current_round <= MAX_ROUNDS:
            print(f"\n{'='*60}")
            print(f"🔄 TOOL CALL ROUND {current_round}/{MAX_ROUNDS}")
            print(f"{'='*60}")

            # Add AI's response to message history
            messages.append({"role": "assistant", "content": current_response.content})

            # Execute all tool calls from current response
            tool_results = []
            for content_block in current_response.content:
                if content_block.type == "tool_use":
                    print(f"  🔧 Tool: {content_block.name}")
                    print(f"  📥 Input: {content_block.input}")

                    tool_result = tool_manager.execute_tool(
                        content_block.name,
                        **content_block.input
                    )

                    print(f"  ✅ Result preview: {str(tool_result)[:100]}...")
                    print()

                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": content_block.id,
                        "content": tool_result
                    })

            # Add tool results as user message
            if tool_results:
                messages.append({"role": "user", "content": tool_results})

            # Determine if tools should be included in next API call
            # Include tools only if we haven't reached max rounds yet
            include_tools = (current_round < MAX_ROUNDS)

            # Prepare API call parameters
            api_params = {
                **self.base_params,
                "messages": messages,
                "system": base_params["system"]
            }

            # Add tools if this isn't the final round
            if include_tools and "tools" in base_params:
                api_params["tools"] = base_params["tools"]
                api_params["tool_choice"] = base_params.get("tool_choice", {"type": "auto"})
                print(f"  🔧 Tools ENABLED for next API call (can call more tools)")
            else:
                print(f"  🚫 Tools DISABLED for next API call (final round)")

            # Make API call
            print(f"  📡 Making API call to Claude...")
            current_response = self.client.messages.create(**api_params)
            print(f"  📨 Response received: stop_reason = {current_response.stop_reason}")

            # Check if we should continue to next round
            # Stop if: (a) no more tool_use, or (b) max rounds reached
            if current_response.stop_reason != "tool_use":
                print(f"\n  ✅ TERMINATING: Claude responded with text (no more tools needed)")
                break  # Claude stopped using tools, we're done

            if current_round >= MAX_ROUNDS:
                print(f"\n  ⚠️  TERMINATING: Maximum rounds ({MAX_ROUNDS}) reached")
                break  # Reached maximum rounds

            print(f"\n  ➡️  CONTINUING to Round {current_round + 1}")
            current_round += 1

        # Return final response text
        return current_response.content[0].text