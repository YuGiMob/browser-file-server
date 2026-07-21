"""
MIME type detection utilities.
"""

import mimetypes
from typing import Optional


# Additional MIME types not in system registry
CUSTOM_MIME_TYPES = {
    '.js': 'application/javascript',
    '.mjs': 'application/javascript',
    '.cjs': 'application/javascript',
    '.jsx': 'text/jsx',
    '.tsx': 'text/tsx',
    '.vue': 'text/x-vue',
    '.svelte': 'text/x-svelte',
    '.ts': 'application/typescript',
    '.json': 'application/json',
    '.yaml': 'text/yaml',
    '.yml': 'text/yaml',
    '.toml': 'text/toml',
    '.md': 'text/markdown',
    '.markdown': 'text/markdown',
    '.rst': 'text/x-rst',
    '.asciidoc': 'text/x-asciidoc',
    '.adoc': 'text/x-asciidoc',
    '.log': 'text/plain',
    '.csv': 'text/csv',
    '.tsv': 'text/tab-separated-values',
    '.sh': 'text/x-shellscript',
    '.bash': 'text/x-shellscript',
    '.zsh': 'text/x-shellscript',
    '.fish': 'text/x-shellscript',
    '.py': 'text/x-python',
    '.pyw': 'text/x-python',
    '.rb': 'text/x-ruby',
    '.pl': 'text/x-perl',
    '.php': 'text/x-php',
    '.go': 'text/x-go',
    '.rs': 'text/x-rust',
    '.java': 'text/x-java',
    '.kt': 'text/x-kotlin',
    '.swift': 'text/x-swift',
    '.c': 'text/x-c',
    '.h': 'text/x-c',
    '.cpp': 'text/x-c++',
    '.hpp': 'text/x-c++',
    '.cc': 'text/x-c++',
    '.cs': 'text/x-csharp',
    '.sql': 'text/x-sql',
    '.r': 'text/x-r',
    '.lua': 'text/x-lua',
    '.vim': 'text/x-vim',
    '.el': 'text/x-emacs-lisp',
    '.clj': 'text/x-clojure',
    '.ex': 'text/x-elixir',
    '.exs': 'text/x-elixir',
    '.erl': 'text/x-erlang',
    '.hs': 'text/x-haskell',
    '.dart': 'text/x-dart',
    '.scala': 'text/x-scala',
    '.groovy': 'text/x-groovy',
    '.gradle': 'text/x-groovy',
    '.dockerfile': 'text/x-dockerfile',
    '.makefile': 'text/x-makefile',
    '.cmake': 'text/x-cmake',
    '.ini': 'text/x-ini',
    '.conf': 'text/x-config',
    '.cfg': 'text/x-config',
    '.env': 'text/x-env',
    '.gitignore': 'text/x-gitignore',
    '.gitattributes': 'text/x-gitattributes',
    '.editorconfig': 'text/x-editorconfig',
    '.diff': 'text/x-diff',
    '.patch': 'text/x-diff',
}

TEXT_EXTENSIONS = set(CUSTOM_MIME_TYPES.keys()) | {
    '.txt', '.bash', '.zsh', '.fish', '.pyw', '.mjs', '.cjs',
    '.scss', '.sass', '.less', '.rtf',
    '.vb', '.pm', '.R',
    '.env.example', '.env.local',
    '.astro',
    '.properties',
    '.textile', '.org', '.tex', '.latex',
}

# Text MIME types
TEXT_MIME_TYPES = {
    'text/',
    'application/json',
    'application/xml',
    'application/javascript',
    'application/typescript',
    'application/x-yaml',
    'application/yaml',
    'application/x-shellscript',
    'application/x-httpd-php',
}

# Binary MIME types that should be previewed
IMAGE_MIME_TYPES = {
    'image/png',
    'image/jpeg',
    'image/gif',
    'image/webp',
    'image/svg+xml',
    'image/bmp',
    'image/x-icon',
    'image/tiff',
}

VIDEO_MIME_TYPES = {
    'video/mp4',
    'video/webm',
    'video/ogg',
    'video/quicktime',
    'video/x-msvideo',
    'video/x-matroska',
    'video/x-flv',
}

AUDIO_MIME_TYPES = {
    'audio/mpeg',
    'audio/wav',
    'audio/ogg',
    'audio/flac',
    'audio/aac',
    'audio/x-wma',
    'audio/mp4',
}

ARCHIVE_MIME_TYPES = {
    'application/zip',
    'application/x-tar',
    'application/gzip',
    'application/x-bzip2',
    'application/x-xz',
    'application/x-7z-compressed',
    'application/x-rar-compressed',
}


# Binary file extension sets (used across modules)
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".bmp", ".ico", ".tiff"}
VIDEO_EXTENSIONS = {".mp4", ".webm", ".ogg", ".mov", ".avi", ".mkv", ".flv", ".wmv"}
AUDIO_EXTENSIONS = {".mp3", ".wav", ".ogg", ".flac", ".aac", ".wma", ".m4a"}
ARCHIVE_EXTENSIONS = {".zip", ".tar", ".gz", ".bz2", ".xz", ".7z", ".rar"}


def guess_mime_type(filename: str) -> Optional[str]:
    """
    Guess MIME type from filename.

    Args:
        filename: Filename or path

    Returns:
        MIME type string or None
    """
    # Check custom types first
    ext = get_extension(filename)
    if ext in CUSTOM_MIME_TYPES:
        return CUSTOM_MIME_TYPES[ext]

    # Fall back to system mimetypes
    mime_type, _ = mimetypes.guess_type(filename)
    return mime_type


def get_extension(filename: str) -> str:
    """
    Get file extension in lowercase.

    Args:
        filename: Filename or path

    Returns:
        Lowercase extension with dot (e.g., '.txt')
    """
    # Handle special filenames
    basename = filename.rsplit('/', 1)[-1].rsplit('\\', 1)[-1]
    lower = basename.lower()
    if lower in ('makefile', 'dockerfile', 'cmakelists.txt', '.gitignore', '.env'):
        if lower.startswith('.'):
            return lower
        return '.' + lower

    # Get extension
    if '.' in basename:
        return '.' + basename.rsplit('.', 1)[1].lower()
    return ''


def is_text_mime_type(mime_type: Optional[str]) -> bool:
    """
    Check if a MIME type represents text content.

    Args:
        mime_type: MIME type string

    Returns:
        True if the MIME type is text
    """
    if not mime_type:
        return False

    for text_prefix in TEXT_MIME_TYPES:
        if text_prefix.endswith('/'):
            if mime_type.startswith(text_prefix):
                return True
        elif mime_type == text_prefix:
            return True

    return False


def is_image_mime_type(mime_type: Optional[str]) -> bool:
    """Check if MIME type is an image."""
    return mime_type in IMAGE_MIME_TYPES
def get_content_disposition(filename: str, mime_type: Optional[str] = None) -> str:
    """
    Get Content-Disposition header value.

    Args:
        filename: Filename
        mime_type: MIME type

    Returns:
        Content-Disposition header value
    """
    # For text and inline-viewable types, use inline
    if mime_type and (is_text_mime_type(mime_type) or is_image_mime_type(mime_type)):
        disposition = 'inline'
    else:
        disposition = 'attachment'

    # Encode filename for header
    from urllib.parse import quote
    encoded_name = quote(filename)

    return f'{disposition}; filename="{encoded_name}"; filename*=UTF-8\'\'{encoded_name}'
