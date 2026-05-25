"""
Phase 4 — Presentation Layer (UI/API).

Keep this module lightweight: do not import Flask apps here, or any
`from phase4 import ...` will require flask on production (Render FastAPI).
Import submodules directly, e.g. `from phase4.ui_components import UIComponents`.
"""

from .ui_components import UIComponents

__all__ = ["UIComponents"]


def __getattr__(name: str):
    """Lazy imports for optional Flask/CLI stacks (local dev only)."""
    if name == "create_app":
        from .web_app import create_app

        return create_app
    if name == "CLIInterface":
        from .cli_interface import CLIInterface

        return CLIInterface
    if name == "APIEndpoints":
        from .api_endpoints import APIEndpoints

        return APIEndpoints
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
