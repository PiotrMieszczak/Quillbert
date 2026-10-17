class DomainError(Exception):
    """Base for errors the HTTP layer maps to a status code."""


class NotFound(DomainError):
    pass


class ValidationFailed(DomainError):
    pass


class UnsupportedFileType(DomainError):
    """The file's extension or content is not one the library accepts (415)."""


class FileTooLarge(DomainError):
    """The file exceeds the upload limit (413)."""
