from dataclasses import dataclass
from typing import BinaryIO, Protocol


@dataclass(frozen=True)
class StoredFile:
    key: str
    sha256: str
    size: int


class FileStore(Protocol):
    def put(self, source: BinaryIO, *, max_bytes: int) -> StoredFile:
        """Stream `source` into storage under a new, unique key.

        The sha256 is computed while streaming. Raises FileTooLarge, leaving nothing
        behind, once more than `max_bytes` have been read.
        """
        ...

    def delete(self, key: str) -> None:
        """Remove a stored file. A key that is already gone is not an error."""
        ...
