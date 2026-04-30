"""Project-wide constants. Never hardcode these values elsewhere."""

ALLOWED_EXTENSIONS: set[str] = {"pdf", "docx", "txt"}

MAX_FILE_SIZE_MB: int = 10
MAX_FILE_SIZE_BYTES: int = MAX_FILE_SIZE_MB * 1024 * 1024

MIN_EXTRACTED_TEXT_LENGTH: int = 50  # characters
