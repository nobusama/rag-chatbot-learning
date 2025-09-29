# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **Course Materials RAG (Retrieval-Augmented Generation) System** - a full-stack web application that enables users to query course materials and receive AI-powered, context-aware responses. The system uses ChromaDB for vector storage, Anthropic's Claude API for response generation, and FastAPI with a vanilla JavaScript frontend.

## Running the Application

### Prerequisites
- Python 3.13+
- uv package manager
- Anthropic API key in `.env` file:
  ```
  ANTHROPIC_API_KEY=your_key_here
  ```

### Commands

**Start the application:**
```bash
./run.sh
```
This starts the FastAPI server on port 8000 with auto-reload enabled.

**Manual start:**
```bash
cd backend
uv run uvicorn app:app --reload --port 8000
```

**Install dependencies:**
```bash
uv sync
```

**Access points:**
- Web UI: http://localhost:8000
- API docs (Swagger): http://localhost:8000/docs

## Architecture Overview

### Request Flow: Tool-Based RAG Pattern

The system implements a **tool-based RAG architecture** where Claude autonomously decides when to search:

```
User Query → FastAPI → RAGSystem → Claude API (with tools)
                                      ↓
                                   Tool Use Decision
                                      ↓
                          CourseSearchTool → VectorStore → ChromaDB
                                      ↓
                                Search Results
                                      ↓
                          Claude API (final answer generation)
                                      ↓
                          Response + Sources → User
```

**Key characteristic:** This is NOT a traditional RAG where retrieval always happens first. Claude receives tool definitions and decides whether to call `search_course_content` based on the query type.

### Core Components

**Backend (`backend/`):**
- `app.py` - FastAPI server, endpoints: `/api/query`, `/api/courses`
- `rag_system.py` - **Main orchestrator**: coordinates search tools, AI generation, session management
- `vector_store.py` - ChromaDB wrapper with two collections:
  - `course_catalog`: Course metadata (titles, instructors, lessons)
  - `course_content`: Text chunks (800 chars, 100 char overlap)
- `ai_generator.py` - Anthropic Claude API client (claude-sonnet-4 model)
- `search_tools.py` - Tool definitions and execution:
  - `CourseSearchTool`: Semantic search with course/lesson filtering
  - `ToolManager`: Registers and executes tools
- `document_processor.py` - Parses course documents, performs sentence-based chunking
- `session_manager.py` - Conversation history (max 2 exchanges)
- `config.py` - Configuration from environment variables
- `models.py` - Pydantic models: `Course`, `Lesson`, `CourseChunk`

**Frontend (`frontend/`):**
- `index.html` - Single-page chat interface
- `script.js` - Handles API calls, message rendering, session management
- `style.css` - Dark theme styling

### Data Model

**Course Document Format** (in `docs/`)

Expected text file structure:
```
Course Title: [title]
Course Link: [url]
Course Instructor: [name]

Lesson 0: [lesson title]
Lesson Link: [url]
[lesson content...]

Lesson 1: [lesson title]
Lesson Link: [url]
[lesson content...]
```

**Document Processing Pipeline:**
1. Parse metadata (title, link, instructor)
2. Split by lesson markers (`Lesson N:`)
3. Chunk each lesson into 800-char segments with 100-char overlap
4. Add context to chunks: `"Course {title} Lesson {N} content: {text}"`
5. Store in ChromaDB with embeddings (all-MiniLM-L6-v2)

### Vector Search Strategy

**Two-step search process:**
1. **Course resolution** (if course_name provided):
   - Semantic search on `course_catalog` collection
   - Finds best matching course title (handles partial matches like "MCP" → full title)
2. **Content search**:
   - Semantic search on `course_content` collection
   - Filters by resolved course_title and/or lesson_number
   - Returns top 5 chunks by default

### AI Generation Flow

**Two API calls per query with tool use:**

1. **First call**: Send query with tool definitions
   - Claude decides whether to use `search_course_content`
   - If tool used: Returns `stop_reason: "tool_use"`

2. **Tool execution**:
   - `ToolManager.execute_tool()` runs the search
   - Results formatted with course/lesson context
   - Sources tracked in `CourseSearchTool.last_sources`

3. **Second call**: Send tool results back to Claude
   - Claude synthesizes final answer from search results
   - Returns natural language response

**System prompt characteristics** (in `ai_generator.py`):
- Use search tool for course-specific questions only
- Maximum one search per query
- No meta-commentary about search process
- Brief, educational responses with examples

### Session Management

- Each user gets a unique `session_id`
- Conversation history limited to **2 exchanges** (4 messages total)
- History formatted as: `"User: {query}\nAssistant: {response}"`
- Included in system prompt context for follow-up questions

## Adding New Course Materials

1. Create a text file in `docs/` following the format above
2. On next startup, `app.py` automatically loads all `.txt`, `.pdf`, `.docx` files from `docs/`
3. System checks existing course titles and skips duplicates
4. New courses are chunked and added to ChromaDB

**Manual data clearing:**
```python
# In Python shell or add to app.py
rag_system.add_course_folder("../docs", clear_existing=True)
```

## Configuration

**Key settings in `config.py`:**
- `ANTHROPIC_MODEL`: "claude-sonnet-4-20250514"
- `EMBEDDING_MODEL`: "all-MiniLM-L6-v2"
- `CHUNK_SIZE`: 800 characters
- `CHUNK_OVERLAP`: 100 characters
- `MAX_RESULTS`: 5 search results
- `MAX_HISTORY`: 2 conversation exchanges
- `CHROMA_PATH`: "./chroma_db" (relative to backend/)

## Common Modification Patterns

**To change chunk size:** Edit `CHUNK_SIZE` and `CHUNK_OVERLAP` in `config.py`, then rebuild database

**To modify search behavior:** Edit `CourseSearchTool.execute()` in `search_tools.py`

**To adjust AI prompt:** Edit `AIGenerator.SYSTEM_PROMPT` in `ai_generator.py`

**To add new tools:**
1. Create class inheriting from `Tool` in `search_tools.py`
2. Implement `get_tool_definition()` and `execute()`
3. Register with `ToolManager` in `rag_system.py`

**To change number of search results:** Modify `MAX_RESULTS` in `config.py` or pass `limit` parameter to `VectorStore.search()`
- Add to memory. Try "Always use descriptive variable names"