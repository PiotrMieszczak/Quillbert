import hashlib
import io
from pathlib import Path

import pytest
from app.adapters.files import LocalDiskFileStore
from app.domain.shared import FileTooLarge

MB = 1024 * 1024


def _files_under(root: Path) -> list[Path]:
    return [path for path in root.rglob("*") if path.is_file()]


def test_put_stores_the_bytes_and_reports_hash_and_size(tmp_path: Path) -> None:
    store = LocalDiskFileStore(tmp_path)
    data = b"%PDF-1.7 hello"

    stored = store.put(io.BytesIO(data), max_bytes=MB)

    assert stored.sha256 == hashlib.sha256(data).hexdigest()
    assert stored.size == len(data)
    on_disk = tmp_path / stored.key[:2] / stored.key
    assert on_disk.read_bytes() == data


def test_every_put_gets_its_own_key(tmp_path: Path) -> None:
    store = LocalDiskFileStore(tmp_path)
    first = store.put(io.BytesIO(b"same"), max_bytes=MB)
    second = store.put(io.BytesIO(b"same"), max_bytes=MB)
    assert first.key != second.key
    assert first.sha256 == second.sha256


def test_an_oversize_file_is_rejected_and_leaves_nothing_behind(tmp_path: Path) -> None:
    store = LocalDiskFileStore(tmp_path)
    with pytest.raises(FileTooLarge):
        store.put(io.BytesIO(b"x" * (MB + 1)), max_bytes=MB)
    assert _files_under(tmp_path) == []


def test_a_file_exactly_at_the_limit_is_accepted(tmp_path: Path) -> None:
    stored = LocalDiskFileStore(tmp_path).put(io.BytesIO(b"x" * MB), max_bytes=MB)
    assert stored.size == MB


def test_delete_removes_the_file_and_tolerates_a_missing_one(tmp_path: Path) -> None:
    store = LocalDiskFileStore(tmp_path)
    stored = store.put(io.BytesIO(b"data"), max_bytes=MB)
    store.delete(stored.key)
    store.delete(stored.key)
    assert _files_under(tmp_path) == []


@pytest.mark.parametrize("key", ["../outside", "/etc/passwd", "short", "g" * 32])
def test_delete_refuses_keys_that_are_not_ours(tmp_path: Path, key: str) -> None:
    with pytest.raises(ValueError):
        LocalDiskFileStore(tmp_path).delete(key)
