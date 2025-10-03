import os
import re
from typing import List, Tuple, Optional
from models import Course, Lesson, CourseChunk

class DocumentProcessor:
    """Processes course documents and extracts structured information"""

    # Constants for document parsing
    METADATA_START_LINE = 3
    METADATA_MAX_LINES = 4

    def __init__(self, chunk_size: int, chunk_overlap: int):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def read_file(self, file_path: str) -> str:
        """Read content from file with UTF-8 encoding"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()
        except UnicodeDecodeError:
            # If UTF-8 fails, try with error handling
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
                return file.read()

    def chunk_text(self, text: str) -> List[str]:
        """Split text into sentence-based chunks with overlap using config settings"""

        # Clean up the text
        text = re.sub(r'\s+', ' ', text.strip())  # Normalize whitespace

        # Split into sentences
        sentences = self._split_into_sentences(text)

        chunks = []
        i = 0

        while i < len(sentences):
            current_chunk = []
            current_size = 0

            # Build chunk starting from sentence i
            for j in range(i, len(sentences)):
                sentence = sentences[j]

                # Calculate size with space
                space_size = 1 if current_chunk else 0
                total_addition = len(sentence) + space_size

                # Check if adding this sentence would exceed chunk size
                if current_size + total_addition > self.chunk_size and current_chunk:
                    break

                current_chunk.append(sentence)
                current_size += total_addition

            # Add chunk if we have content
            if current_chunk:
                chunks.append(' '.join(current_chunk))

                # Calculate next starting position with overlap
                next_i = self._calculate_next_position(
                    current_chunk,
                    i,
                    len(current_chunk)
                )
                i = next_i
            else:
                # No sentences fit, move to next
                i += 1

        return chunks

    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences handling common abbreviations"""
        # Better sentence splitting that handles abbreviations
        # This regex looks for periods followed by whitespace and capital letters
        # but ignores common abbreviations
        sentence_endings = re.compile(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\!|\?)\s+(?=[A-Z])')
        sentences = sentence_endings.split(text)

        # Clean sentences
        return [s.strip() for s in sentences if s.strip()]

    def _calculate_next_position(self, current_chunk: List[str], current_i: int, chunk_length: int) -> int:
        """Calculate next starting position considering overlap"""
        if not hasattr(self, 'chunk_overlap') or self.chunk_overlap <= 0:
            return current_i + chunk_length

        # Calculate overlap sentences
        overlap_size = 0
        overlap_sentences = 0

        # Count backwards from end of current chunk
        for k in range(len(current_chunk) - 1, -1, -1):
            sentence_len = len(current_chunk[k]) + (1 if k < len(current_chunk) - 1 else 0)
            if overlap_size + sentence_len <= self.chunk_overlap:
                overlap_size += sentence_len
                overlap_sentences += 1
            else:
                break

        # Move start position considering overlap
        next_start = current_i + chunk_length - overlap_sentences
        return max(next_start, current_i + 1)  # Ensure we make progress

    def process_course_document(self, file_path: str) -> Tuple[Course, List[CourseChunk]]:
        """
        Process a course document with expected format:
        Line 1: Course Title: [title]
        Line 2: Course Link: [url]
        Line 3: Course Instructor: [instructor]
        Following lines: Lesson markers and content
        """
        content = self.read_file(file_path)
        filename = os.path.basename(file_path)
        lines = content.strip().split('\n')

        # Parse course metadata
        course_title, course_link, instructor_name = self._parse_course_metadata(lines, filename)

        # Create course object
        course = Course(
            title=course_title,
            course_link=course_link,
            instructor=instructor_name if instructor_name != "Unknown" else None
        )

        # Process lessons and create chunks
        start_index = self._get_content_start_index(lines)
        course_chunks = self._process_lessons(lines, start_index, course)

        # Handle case where no lessons were found
        if not course_chunks and len(lines) > 2:
            course_chunks = self._handle_no_lessons_case(lines, start_index, course)

        return course, course_chunks

    def _parse_course_metadata(self, lines: List[str], filename: str) -> Tuple[str, Optional[str], str]:
        """
        Extract course metadata from document lines.

        Returns:
            Tuple of (course_title, course_link, instructor_name)
        """
        course_title = filename  # Default fallback
        course_link = None
        instructor_name = "Unknown"

        # Parse course title from first line
        if len(lines) >= 1 and lines[0].strip():
            course_title = self._extract_title(lines[0])

        # Parse remaining metadata lines
        course_link, instructor_name = self._extract_link_and_instructor(
            lines, course_link, instructor_name
        )

        return course_title, course_link, instructor_name

    def _extract_title(self, first_line: str) -> str:
        """Extract course title from first line"""
        title_match = re.match(r'^Course Title:\s*(.+)$', first_line.strip(), re.IGNORECASE)
        if title_match:
            return title_match.group(1).strip()
        return first_line.strip()

    def _extract_link_and_instructor(
        self,
        lines: List[str],
        default_link: Optional[str],
        default_instructor: str
    ) -> Tuple[Optional[str], str]:
        """Extract course link and instructor from metadata lines"""
        course_link = default_link
        instructor_name = default_instructor

        # Check first few lines for metadata
        for i in range(1, min(len(lines), self.METADATA_MAX_LINES)):
            line = lines[i].strip()
            if not line:
                continue

            # Try to match course link
            link_match = re.match(r'^Course Link:\s*(.+)$', line, re.IGNORECASE)
            if link_match:
                course_link = link_match.group(1).strip()
                continue

            # Try to match instructor
            instructor_match = re.match(r'^Course Instructor:\s*(.+)$', line, re.IGNORECASE)
            if instructor_match:
                instructor_name = instructor_match.group(1).strip()
                continue

        return course_link, instructor_name

    def _get_content_start_index(self, lines: List[str]) -> int:
        """Determine where course content starts (after metadata)"""
        start_index = self.METADATA_START_LINE
        if len(lines) > self.METADATA_START_LINE and not lines[self.METADATA_START_LINE].strip():
            start_index = self.METADATA_START_LINE + 1  # Skip empty line after instructor
        return start_index

    def _process_lessons(
        self,
        lines: List[str],
        start_index: int,
        course: Course
    ) -> List[CourseChunk]:
        """Process all lessons in the document"""
        course_chunks = []
        chunk_counter = 0

        current_lesson_data = None
        lesson_content = []

        i = start_index
        while i < len(lines):
            line = lines[i]

            # Check for lesson markers
            lesson_match = re.match(r'^Lesson\s+(\d+):\s*(.+)$', line.strip(), re.IGNORECASE)

            if lesson_match:
                # Process previous lesson if it exists
                if current_lesson_data is not None and lesson_content:
                    chunks = self._process_single_lesson(
                        current_lesson_data,
                        lesson_content,
                        course,
                        chunk_counter
                    )
                    course_chunks.extend(chunks)
                    chunk_counter += len(chunks)

                # Start new lesson
                lesson_number = int(lesson_match.group(1))
                lesson_title = lesson_match.group(2).strip()
                lesson_link = None

                # Check if next line is a lesson link
                if i + 1 < len(lines):
                    next_line = lines[i + 1].strip()
                    link_match = re.match(r'^Lesson Link:\s*(.+)$', next_line, re.IGNORECASE)
                    if link_match:
                        lesson_link = link_match.group(1).strip()
                        i += 1  # Skip the link line

                current_lesson_data = (lesson_number, lesson_title, lesson_link)
                lesson_content = []
            else:
                # Add line to current lesson content
                lesson_content.append(line)

            i += 1

        # Process the last lesson
        if current_lesson_data is not None and lesson_content:
            chunks = self._process_single_lesson(
                current_lesson_data,
                lesson_content,
                course,
                chunk_counter
            )
            course_chunks.extend(chunks)

        return course_chunks

    def _process_single_lesson(
        self,
        lesson_data: Tuple[int, str, Optional[str]],
        lesson_content: List[str],
        course: Course,
        chunk_start_index: int
    ) -> List[CourseChunk]:
        """
        Process a single lesson: create lesson object and generate chunks.

        Args:
            lesson_data: Tuple of (lesson_number, lesson_title, lesson_link)
            lesson_content: List of content lines
            course: Course object to add lesson to
            chunk_start_index: Starting index for chunk numbering

        Returns:
            List of CourseChunk objects for this lesson
        """
        lesson_number, lesson_title, lesson_link = lesson_data

        # Join and clean lesson content
        lesson_text = '\n'.join(lesson_content).strip()
        if not lesson_text:
            return []

        # Add lesson to course
        lesson = Lesson(
            lesson_number=lesson_number,
            title=lesson_title,
            lesson_link=lesson_link
        )
        course.lessons.append(lesson)

        # Create chunks for this lesson
        return self._create_lesson_chunks(
            lesson_text,
            course.title,
            lesson_number,
            chunk_start_index
        )

    def _create_lesson_chunks(
        self,
        lesson_text: str,
        course_title: str,
        lesson_number: int,
        chunk_start_index: int
    ) -> List[CourseChunk]:
        """Create chunks from lesson text with proper context"""
        chunks = self.chunk_text(lesson_text)
        course_chunks = []

        for idx, chunk in enumerate(chunks):
            # Add context to chunk
            chunk_with_context = f"Course {course_title} Lesson {lesson_number} content: {chunk}"

            course_chunk = CourseChunk(
                content=chunk_with_context,
                course_title=course_title,
                lesson_number=lesson_number,
                chunk_index=chunk_start_index + idx
            )
            course_chunks.append(course_chunk)

        return course_chunks

    def _handle_no_lessons_case(
        self,
        lines: List[str],
        start_index: int,
        course: Course
    ) -> List[CourseChunk]:
        """Handle case where document has no lesson markers"""
        remaining_content = '\n'.join(lines[start_index:]).strip()
        if not remaining_content:
            return []

        chunks = self.chunk_text(remaining_content)
        course_chunks = []

        for idx, chunk in enumerate(chunks):
            course_chunk = CourseChunk(
                content=chunk,
                course_title=course.title,
                chunk_index=idx
            )
            course_chunks.append(course_chunk)

        return course_chunks
