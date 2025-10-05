# Course Materials RAG System

A Retrieval-Augmented Generation (RAG) system designed to answer questions about course materials using semantic search and AI-powered responses.

## Overview

This application is a full-stack web application that enables users to query course materials and receive intelligent, context-aware responses. It uses ChromaDB for vector storage, Anthropic's Claude for AI generation, and provides a web interface for interaction.


## Prerequisites

- Python 3.13 or higher
- uv (Python package manager)
- An Anthropic API key (for Claude AI)
- **For Windows**: Use Git Bash to run the application commands - [Download Git for Windows](https://git-scm.com/downloads/win)

## Installation

1. **Install uv** (if not already installed)
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. **Install Python dependencies**
   ```bash
   uv sync
   ```

3. **Set up environment variables**
   
   Create a `.env` file in the root directory:
   ```bash
   ANTHROPIC_API_KEY=your_anthropic_api_key_here
   ```

## Running the Application

### Quick Start

Use the provided shell script:
```bash
chmod +x run.sh
./run.sh
```

### Manual Start

```bash
cd backend
uv run uvicorn app:app --reload --port 8000
```

The application will be available at:
- Web Interface: `http://localhost:8000`
- API Documentation: `http://localhost:8000/docs`

## Example Queries

Once the application is running, you can try these example queries to explore the system's capabilities:

### General Questions
- "What is MCP?"
- "What courses are available?"
- "Who teaches the course on MCP?"

### Course-Specific Questions
- "Explain the key concepts in Lesson 1 of the MCP course"
- "What are the main topics covered in the prompt engineering course?"
- "How does the MCP course explain server architecture?"

### Follow-up Questions
The system maintains conversation history, so you can ask follow-up questions like:
- "Can you give me an example?" (after receiving an explanation)
- "Tell me more about that" (to dive deeper into a topic)
- "What's covered in the next lesson?" (to continue learning)

### Technical Queries
- "What are the prerequisites for the MCP course?"
- "Show me examples from the prompt engineering lessons"
- "What tools are discussed in Lesson 3?"

**Tip:** The AI will automatically search course content when needed and provide direct answers for general questions. Try both types to see the difference!

## 🤖 Claude Code Integration

This repository is integrated with Claude Code! You can:
- Mention @claude in any PR or issue comment to get AI assistance
- Request bug fixes, code reviews, documentation updates, and more
- Claude can help implement features, write tests, and improve code quality
- See [Claude Code](https://claude.com/claude-code) for more information

## Project Structure

```
├── backend/          # FastAPI backend application
│   ├── app.py       # Main FastAPI server and endpoints
│   ├── rag_system.py # RAG orchestration and tool management
│   ├── vector_store.py # ChromaDB wrapper for vector search
│   ├── ai_generator.py # Anthropic Claude API client
│   ├── search_tools.py # Tool definitions and execution
│   ├── document_processor.py # Course document parsing and chunking
│   ├── session_manager.py # Conversation history management
│   ├── config.py    # Configuration settings
│   ├── models.py    # Pydantic data models
│   └── tests/       # Unit and integration tests
├── frontend/         # Vanilla JavaScript frontend
│   ├── index.html   # Single-page chat interface
│   ├── script.js    # API calls and UI logic
│   └── style.css    # Dark theme styling
├── docs/            # Course materials (text files)
├── scripts/         # Utility scripts
│   ├── format.sh    # Code formatting script
│   └── quality-check.sh # Code quality checks
├── .github/         # GitHub workflows and actions
│   └── workflows/   # CI/CD and Claude Code workflows
└── CLAUDE.md        # Instructions for Claude Code agent
```

## Adding Course Materials

To add new course materials to the system:

1. **Prepare your course document** in one of these formats:
   - Text file (`.txt`)
   - PDF (`.pdf`)
   - Word document (`.docx`)

2. **Format your document** with this structure:
   ```
   Course Title: [Your Course Title]
   Course Link: [URL]
   Course Instructor: [Instructor Name]

   Lesson 0: [Lesson Title]
   Lesson Link: [URL]
   [Lesson content...]

   Lesson 1: [Next Lesson Title]
   Lesson Link: [URL]
   [Lesson content...]
   ```

3. **Place the file** in the `docs/` directory

4. **Restart the application** - The system will automatically:
   - Detect new course files
   - Parse course metadata and lessons
   - Chunk content into 800-character segments
   - Generate embeddings and store in ChromaDB
   - Skip duplicates based on course title

**Note:** The database persists in `backend/chroma_db/`. To rebuild from scratch, delete this directory before restarting.

## Development

### Running Tests

```bash
cd backend
uv run pytest tests/
```

### Code Quality

Format code:
```bash
./scripts/format.sh
```

Run quality checks:
```bash
./scripts/quality-check.sh
```

### API Endpoints

- `POST /api/query` - Submit a question and receive AI-generated answers
- `GET /api/courses` - List all available courses

See full API documentation at `http://localhost:8000/docs` when running.

### Architecture Notes

This system uses a **tool-based RAG architecture** where:
- Claude autonomously decides when to search course content
- General questions get direct answers without unnecessary retrieval
- Course-specific queries trigger semantic search via tool use
- Two ChromaDB collections: `course_catalog` (metadata) and `course_content` (chunks)

See `CLAUDE.md` for detailed architecture documentation.

## Contributing

When contributing to this project:

1. Follow the existing code style (use `./scripts/format.sh`)
2. Run quality checks before committing (`./scripts/quality-check.sh`)
3. Update tests for new features
4. Update documentation as needed
5. You can mention @claude in PRs for code review assistance

## Troubleshooting

**Application won't start:**
- Verify Python 3.13+ is installed: `python --version`
- Check that `.env` file exists with valid `ANTHROPIC_API_KEY`
- Ensure uv is installed: `uv --version`

**No search results:**
- Verify course documents are in `docs/` directory
- Check `backend/chroma_db/` exists (created on first run)
- Restart application to reindex documents

**Windows users:**
- Use Git Bash to run shell scripts
- If `./run.sh` fails, use the manual start method

## License

This project is licensed under the MIT License.

