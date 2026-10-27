"""User-facing wording for playback failures. Backend detail belongs in the log, not the UI."""

from __future__ import annotations

from dataclasses import dataclass

ERROR_KINDS = ("format", "resource", "access", "network", "other")


@dataclass(frozen=True, slots=True)
class FriendlyError:
    title: str
    message: str


def describe_error(kind: str, file_name: str) -> FriendlyError:
    """Plain-language title and explanation for an error `kind` from ERROR_KINDS."""
    if kind == "format":
        return FriendlyError(
            "Unsupported format",
            f"“{file_name}” uses a format or codec Aperture can't decode.",
        )
    if kind == "resource":
        return FriendlyError(
            "Can't open this file",
            f"“{file_name}” may have been moved, is still downloading, or is damaged.",
        )
    if kind == "access":
        return FriendlyError(
            "No permission",
            f"Aperture isn't allowed to read “{file_name}”.",
        )
    if kind == "network":
        return FriendlyError(
            "Connection problem",
            f"“{file_name}” is on a network location that stopped responding.",
        )
    return FriendlyError(
        "Playback failed",
        f"Something went wrong while playing “{file_name}”.",
    )
