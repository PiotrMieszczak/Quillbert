import ast
from pathlib import Path

APP = Path(__file__).resolve().parents[2] / "app"

FORBIDDEN_SDKS = {"anthropic", "ollama", "openai", "langchain", "pydantic_ai"}
DATABASE_LIBRARIES = {"sqlalchemy", "psycopg", "alembic"}


def _imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text())
    found: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            found.add(node.module.split(".")[0])
            found.add(node.module)
    return found


def _py_files(package: str) -> list[Path]:
    return list((APP / package).rglob("*.py"))


def test_domain_does_not_import_the_rest_of_the_app() -> None:
    banned = {
        "app.ports",
        "app.application",
        "app.adapters",
        "app.entrypoints",
        "app.composition",
    }
    for path in _py_files("domain"):
        imported = _imports(path)
        leaked = {
            name
            for name in imported
            if any(name == item or name.startswith(f"{item}.") for item in banned)
        }
        assert not leaked, f"{path} imports {leaked}"


def test_application_does_not_import_adapters_or_entrypoints() -> None:
    for path in _py_files("application"):
        imported = _imports(path)
        assert "app.adapters" not in imported
        assert "app.entrypoints" not in imported
        assert not any(name.startswith("app.adapters.") for name in imported)
        assert not any(name.startswith("app.entrypoints.") for name in imported)


def test_entrypoints_do_not_import_adapters() -> None:
    for path in _py_files("entrypoints"):
        imported = _imports(path)
        assert "app.adapters" not in imported
        assert not any(name.startswith("app.adapters.") for name in imported)


def test_database_libraries_only_under_sqlalchemy_adapter() -> None:
    """The domain does not know SQL exists; composition wires the adapter by name."""
    for path in APP.rglob("*.py"):
        hit = _imports(path) & DATABASE_LIBRARIES
        if not hit:
            continue
        location = path.as_posix()
        assert "adapters/persistence/sqlalchemy" in location, (
            f"{path} imports {hit} outside adapters/persistence/sqlalchemy"
        )


def test_openrouter_is_only_named_under_llm_gateway() -> None:
    """BND-002: no other module may know the provider's endpoint."""
    for path in APP.rglob("*.py"):
        if "adapters/llm" not in path.as_posix():
            assert "openrouter.ai" not in path.read_text(), f"{path} names OpenRouter"


def test_provider_sdks_only_under_llm_gateway() -> None:
    """BND-002: the Gateway is app.adapters.llm."""
    for path in APP.rglob("*.py"):
        imported = _imports(path)
        hit = imported & FORBIDDEN_SDKS
        if not hit:
            continue
        location = path.as_posix()
        assert "adapters/llm" in location, f"{path} imports {hit} outside adapters/llm"
