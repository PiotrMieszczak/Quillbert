import hashlib
import os
import re
import uuid
from pathlib import Path
from typing import BinaryIO

from app.domain.shared import FileTooLarge
from app.ports.files import StoredFile

_KEY = re.compile(r"[0-9a-f]{32}")
_CHUNK = 1024 * 1024
_MB = 1024 * 1024


class LocalDiskFileStore:
    """FileStore on a directory: `<root>/<first two chars>/<key>`.

    The key is a random hex id, never a name from the client, and delete() refuses
    anything else, so no key can point outside the root. Files are written under
    `.incoming/` first and moved into place, so a half-written file is never visible.
    """

    def __init__(self, root: Path) -> None:
        self._root = root

    def put(self, source: BinaryIO, *, max_bytes: int) -> StoredFile:
        key = uuid.uuid4().hex
        incoming = self._root / ".incoming" / key
        incoming.parent.mkdir(parents=True, exist_ok=True)
        digest = hashlib.sha256()
        size = 0
        try:
            with incoming.open("wb") as out:
                while chunk := source.read(_CHUNK):
                    size += len(chunk)
                    if size > max_bytes:
                        raise FileTooLarge(f"file is larger than {max_bytes // _MB} MB")
                    digest.update(chunk)
                    out.write(chunk)
            final = self._path(key)
            final.parent.mkdir(parents=True, exist_ok=True)
            os.replace(incoming, final)
        except BaseException:
            incoming.unlink(missing_ok=True)
            raise
        return StoredFile(key=key, sha256=digest.hexdigest(), size=size)

    def delete(self, key: str) -> None:
        self._path(key).unlink(missing_ok=True)

    def _path(self, key: str) -> Path:
        if not _KEY.fullmatch(key):
            raise ValueError("invalid storage key")
        return self._root / key[:2] / key
