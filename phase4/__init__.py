"""
Phase 4 - Presentation Layer (UI/API)

This module provides the user interface and API endpoints for the
AI-Powered Restaurant Recommendation System.
"""

from .web_app import create_app
from .cli_interface import CLIInterface
from .ui_components import UIComponents
from .api_endpoints import APIEndpoints

__all__ = [
    'create_app',
    'CLIInterface',
    'UIComponents', 
    'APIEndpoints'
]
