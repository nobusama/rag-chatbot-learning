# Backend AI Generator Multi-Tool Refactoring

## Overview
Refactor `backend/ai_generator.py` to support multiple tool calls in separate rounds for handling complex queries that require multi-step reasoning.

## Current Behavior
- **One search per query maximum** (explicitly stated in system prompt)
- Single tool execution cycle:
  1. User query → Claude
  2. Claude decides to use tool → Tool execution
  3. Tool result → Claude
  4. Claude generates final answer → END
- Cannot handle complex queries requiring multiple searches or comparisons

## Desired Behavior
- Support **multiple tool calls across multiple rounds**
- Iterative or recursive tool execution flow:
  1. User query → Claude
  2. Claude uses Tool 1 → Result 1
  3. Claude analyzes Result 1, decides to use Tool 2 → Result 2
  4. Claude uses Tool 3 if needed → Result 3
  5. Claude synthesizes all results → Final answer
- Maximum rounds limit to prevent infinite loops

## Example Use Cases

### Example 1: Course Comparison
```
User: "Are there any other courses that cover the same topic as Lesson 5 of the MCP course?"

Round 1: search_course_content(query="MCP Lesson 5", course_name="MCP")
  → Result: "Lesson 5 covers server implementation, protocol design..."

Round 2: search_course_content(query="server implementation protocol")
  → Result: "No other courses found with this topic"

Round 3: Get course catalog to verify
  → Result: Course list

Final Answer: "Lesson 5 covers server implementation. No other courses in the catalog cover this topic."
```

### Example 2: Detailed Lesson Information
```
User: "What are the details of Lesson 5?"

Round 1: Get course outline
  → Result: Course structure

Round 2: Get specific lesson content with title
  → Result: Detailed lesson information including title

Final Answer: Complete lesson details with title
```

## Implementation Approach

**Dispatch two parallel subagents to brainstorm different approaches:**
- **Approach A**: Simple iterative implementation with while loop
- **Approach B**: More comprehensive recursive implementation

**Do NOT implement code yet** - first explore multiple options and select the best approach.

## Requirements

### Functional Requirements
1. Support maximum N rounds of tool calls (default: 5)
2. Stop when Claude decides not to use tools anymore
3. Maintain conversation context across rounds
4. Handle tool failures gracefully

### Non-Functional Requirements
1. **Backward compatibility**: Existing single-tool queries must still work
2. **No breaking changes**: Don't modify RAG system interface or API endpoints
3. **Performance**: Reasonable timeout for maximum rounds
4. **Testing**: Write tests verifying multi-tool scenarios

## Technical Constraints

### Files to Modify
- `backend/ai_generator.py`:
  - Update `SYSTEM_PROMPT` to allow multiple tool calls
  - Modify `generate_response()` to accept `max_rounds` parameter
  - Refactor `_handle_tool_execution()` to support iteration/recursion

### Files NOT to Modify
- `backend/rag_system.py` (orchestrator should remain unchanged)
- `backend/app.py` (API endpoints unchanged)
- `backend/search_tools.py` (tool definitions unchanged)

## Testing Strategy

### Test Cases to Add
1. **Single tool call** (regression test - ensure backward compatibility)
2. **Sequential tool calls** (2-3 rounds)
3. **Maximum rounds limit** (verify it stops at max_rounds)
4. **No tool use** (general knowledge questions without tools)
5. **Tool failure handling** (graceful degradation)

### Testing Notes
- Focus on **external behavior**, not internal state
- Mock the Anthropic API responses for different scenarios
- Verify conversation history is properly maintained

## Success Criteria

- [ ] Complex queries requiring multiple searches work correctly
- [ ] All existing tests still pass (backward compatibility)
- [ ] New tests for multi-tool scenarios pass
- [ ] Browser verification: Complex query returns accurate answer
- [ ] No performance degradation for simple queries

## Notes

- Start by exploring multiple implementation approaches in parallel
- Choose the simpler approach (Approach A) for initial implementation
- Update system prompt to clarify multi-tool usage guidelines
- Consider adding logging for debugging multi-round flows
- Document the maximum rounds parameter in code comments

## Example Queries to Test

After implementation, test with:
1. "What is MCP?" (should work with 1 tool call - regression test)
2. "What are the details of Lesson 5?" (requires 2 tool calls for title)
3. "Are there any other courses that cover the same topic as Lesson 5?" (requires multiple searches and comparison)
