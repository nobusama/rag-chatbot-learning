from typing import Dict, Any, Optional, Protocol
from abc import ABC, abstractmethod
from vector_store import VectorStore, SearchResults


class Tool(ABC):
    """Abstract base class for all tools"""
    
    @abstractmethod
    def get_tool_definition(self) -> Dict[str, Any]:
        """Return Anthropic tool definition for this tool"""
        pass
    
    @abstractmethod
    def execute(self, **kwargs) -> str:
        """Execute the tool with given parameters"""
        pass


class CourseSearchTool(Tool):
    """Tool for searching course content with semantic course name matching"""
    
    def __init__(self, vector_store: VectorStore):
        self.store = vector_store
        self.last_sources = []  # Track sources from last search
    
    def get_tool_definition(self) -> Dict[str, Any]:
        """Return Anthropic tool definition for this tool"""
        return {
            "name": "search_course_content",
            "description": "Search course materials with smart course name matching and lesson filtering",
            "input_schema": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string", 
                        "description": "What to search for in the course content"
                    },
                    "course_name": {
                        "type": "string",
                        "description": "Course title (partial matches work, e.g. 'MCP', 'Introduction')"
                    },
                    "lesson_number": {
                        "type": "integer",
                        "description": "Specific lesson number to search within (e.g. 1, 2, 3)"
                    }
                },
                "required": ["query"]
            }
        }
    
    def execute(self, query: str, course_name: Optional[str] = None, lesson_number: Optional[int] = None) -> str:
        """
        Execute the search tool with given parameters.
        
        Args:
            query: What to search for
            course_name: Optional course filter
            lesson_number: Optional lesson filter
            
        Returns:
            Formatted search results or error message
        """
        
        # Use the vector store's unified search interface
        results = self.store.search(
            query=query,
            course_name=course_name,
            lesson_number=lesson_number
        )
        
        # Handle errors
        if results.error:
            return results.error
        
        # Handle empty results
        if results.is_empty():
            filter_info = ""
            if course_name:
                filter_info += f" in course '{course_name}'"
            if lesson_number:
                filter_info += f" in lesson {lesson_number}"
            return f"No relevant content found{filter_info}."
        
        # Format and return results
        return self._format_results(results)
    
    def _format_results(self, results: SearchResults) -> str:
        """Format search results with course and lesson context"""
        formatted = []
        sources = []  # Track sources for the UI

        # Create a list of tuples (doc, meta, lesson_num) for sorting
        results_with_lesson = []

        for doc, meta in zip(results.documents, results.metadata):
            course_title = meta.get('course_title', 'unknown')
            lesson_num = meta.get('lesson_number')
            # Use -1 for entries without lesson number so they appear first
            sort_key = lesson_num if lesson_num is not None else -1
            results_with_lesson.append((doc, meta, sort_key))

        # Sort by lesson number
        results_with_lesson.sort(key=lambda x: x[2])

        # Process sorted results
        for doc, meta, _ in results_with_lesson:
            course_title = meta.get('course_title', 'unknown')
            lesson_num = meta.get('lesson_number')

            # Build context header
            header = f"[{course_title}"
            if lesson_num is not None:
                header += f" - Lesson {lesson_num}"
            header += "]"

            # Track source for the UI with link information
            source_dict = {
                "text": course_title,
                "course_link": self.store.get_course_link(course_title),
                "lesson_number": lesson_num  # Include for potential frontend sorting
            }

            if lesson_num is not None:
                source_dict["text"] += f" - Lesson {lesson_num}"
                lesson_link = self.store.get_lesson_link(course_title, lesson_num)
                if lesson_link:
                    source_dict["lesson_link"] = lesson_link

            sources.append(source_dict)

            formatted.append(f"{header}\n{doc}")

        # Store sources for retrieval
        self.last_sources = sources

        return "\n\n".join(formatted)


class CourseOutlineTool(Tool):
    """Tool for getting detailed course outline information"""

    def __init__(self, vector_store: VectorStore):
        self.store = vector_store
        self.last_sources = []

    def get_tool_definition(self) -> Dict[str, Any]:
        """Return Anthropic tool definition for this tool"""
        return {
            "name": "get_course_outline",
            "description": "Get the complete structure and lesson list for a specific course, including course title, course link, and all lessons with their numbers and titles",
            "input_schema": {
                "type": "object",
                "properties": {
                    "course_name": {
                        "type": "string",
                        "description": "Course title (partial matches work, e.g. 'MCP', 'Introduction', 'Claude Code')"
                    }
                },
                "required": ["course_name"]
            }
        }

    def execute(self, course_name: str) -> str:
        """
        Execute the course outline tool to get course structure.

        Args:
            course_name: Course title or partial name to search for

        Returns:
            Formatted course outline with lessons or error message
        """
        import json

        # First resolve the course name using semantic search
        course_title = self.store._resolve_course_name(course_name)

        if not course_title:
            return f"No course found matching '{course_name}'."

        # Get the course metadata from course_catalog
        try:
            results = self.store.course_catalog.get(ids=[course_title])

            if not results or not results['metadatas'] or len(results['metadatas']) == 0:
                return f"Course '{course_title}' found but no metadata available."

            metadata = results['metadatas'][0]
            course_link = metadata.get('course_link', '')
            lessons_json = metadata.get('lessons_json', '[]')
            lessons = json.loads(lessons_json)

            # Build formatted output
            output = self._format_outline(course_title, course_link, lessons)

            # Track sources for UI
            self._build_sources(course_title, course_link, lessons)

            return output

        except Exception as e:
            return f"Error retrieving course outline: {str(e)}"

    def _format_outline(self, course_title: str, course_link: str, lessons: list) -> str:
        """Format the course outline in a readable structure"""
        output = f"Course: {course_title}\n"
        if course_link:
            output += f"Course Link: {course_link}\n"
        output += f"\nLessons ({len(lessons)} total):\n"

        for lesson in lessons:
            lesson_num = lesson.get('lesson_number', 'N/A')
            lesson_title = lesson.get('lesson_title', 'Unknown')
            lesson_link = lesson.get('lesson_link', '')

            output += f"\nLesson {lesson_num}: {lesson_title}"
            if lesson_link:
                output += f"\nLink: {lesson_link}"
            output += "\n"

        return output

    def _build_sources(self, course_title: str, course_link: str, lessons: list):
        """Build source information for UI display"""
        sources = []

        for lesson in lessons:
            lesson_num = lesson.get('lesson_number')
            lesson_link = lesson.get('lesson_link', '')

            source_dict = {
                "text": f"{course_title} - Lesson {lesson_num}",
                "course_link": course_link,
                "lesson_number": lesson_num
            }
            if lesson_link:
                source_dict["lesson_link"] = lesson_link

            sources.append(source_dict)

        # Store sources for retrieval
        self.last_sources = sources


class ToolManager:
    """Manages available tools for the AI"""
    
    def __init__(self):
        self.tools = {}
    
    def register_tool(self, tool: Tool):
        """Register any tool that implements the Tool interface"""
        tool_def = tool.get_tool_definition()
        tool_name = tool_def.get("name")
        if not tool_name:
            raise ValueError("Tool must have a 'name' in its definition")
        self.tools[tool_name] = tool

    
    def get_tool_definitions(self) -> list:
        """Get all tool definitions for Anthropic tool calling"""
        return [tool.get_tool_definition() for tool in self.tools.values()]
    
    def execute_tool(self, tool_name: str, **kwargs) -> str:
        """Execute a tool by name with given parameters"""
        if tool_name not in self.tools:
            return f"Tool '{tool_name}' not found"
        
        return self.tools[tool_name].execute(**kwargs)
    
    def get_last_sources(self) -> list:
        """Get sources from the last search operation"""
        # Check all tools for last_sources attribute
        for tool in self.tools.values():
            if hasattr(tool, 'last_sources') and tool.last_sources:
                return tool.last_sources
        return []

    def reset_sources(self):
        """Reset sources from all tools that track sources"""
        for tool in self.tools.values():
            if hasattr(tool, 'last_sources'):
                tool.last_sources = []