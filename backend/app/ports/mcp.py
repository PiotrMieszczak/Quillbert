from dataclasses import dataclass
from typing import Any, Protocol


class McpError(Exception):
    """The server could not be used: unreachable, too slow, too large or malformed.
    The message never carries the token."""


class AddressRefused(McpError):
    """The URL is not a public HTTPS address (ADR-0031). Callers show one generic
    message for this, so the API cannot be used to probe a network."""


@dataclass(frozen=True)
class McpTool:
    name: str
    # The server's own words: shown to the GM, never to the model.
    description: str
    # `readOnlyHint`, the server's claim about itself. None: it did not say.
    read_only: bool | None
    # The one required string argument a question can be sent as, if there is one.
    query_arg: str | None


class McpClient(Protocol):
    """A user-supplied, untrusted MCP server over streamable HTTP (ADR-0031)."""

    def list_tools(self, url: str, token: str | None) -> list[McpTool]:
        """Raises McpError."""
        ...

    def call_tool(
        self, url: str, token: str | None, name: str, arguments: dict[str, Any]
    ) -> list[str]:
        """The text blocks of the result. Raises McpError."""
        ...
