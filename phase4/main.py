"""
Main Integration Module for Phase 4

Integrates Phase 3 orchestration with Phase 4 presentation layer
and provides the main entry point for the application.
"""

import asyncio
import sys
import os
from typing import Optional

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from phase4.web_app import create_app
from phase4.cli_interface import CLIInterface, CLIConfig
from phase4.api_endpoints import APIEndpoints, APIConfig
from phase4.ui_components import UIComponents, RenderConfig


class Phase4Integration:
    """Main integration class for Phase 4 presentation layer"""
    
    def __init__(self, llm_provider: str = "groq"):
        self.llm_provider = llm_provider
        self.ui_components = UIComponents()
        self.cli_interface = None
        self.api_endpoints = None
        self.web_app = None
    
    def setup_cli(self, config: Optional[CLIConfig] = None) -> CLIInterface:
        """Setup CLI interface"""
        if not config:
            config = CLIConfig(llm_provider=self.llm_provider)
        
        self.cli_interface = CLIInterface(config)
        return self.cli_interface
    
    def setup_api(self, config: Optional[APIConfig] = None) -> APIEndpoints:
        """Setup API endpoints"""
        if not config:
            config = APIConfig(llm_provider=self.llm_provider)
        
        self.api_endpoints = APIEndpoints(config)
        return self.api_endpoints
    
    def setup_web_app(self, config: Optional[APIConfig] = None):
        """Setup web application"""
        if not config:
            config = APIConfig(llm_provider=self.llm_provider)
        
        self.web_app = create_app(config)
        return self.web_app
    
    async def run_cli_demo(self):
        """Run CLI demonstration"""
        print("🚀 Starting CLI Demo...")
        cli = self.setup_cli()
        await cli.run_interactive()
    
    def run_api_server(self, host: str = "0.0.0.0", port: int = 5000, debug: bool = False):
        """Run API server"""
        print(f"🚀 Starting API Server on http://{host}:{port}")
        api_config = APIConfig(
            host=host,
            port=port,
            debug=debug,
            llm_provider=self.llm_provider
        )
        api = self.setup_api(api_config)
        api.run()
    
    def run_web_app(self, host: str = "0.0.0.0", port: int = 5000, debug: bool = False):
        """Run web application"""
        print(f"🚀 Starting Web App on http://{host}:{port}")
        api_config = APIConfig(
            host=host,
            port=port,
            debug=debug,
            llm_provider=self.llm_provider
        )
        app = self.setup_web_app(api_config)
        app.run(host=host, port=port, debug=debug)
    
    def get_system_status(self) -> dict:
        """Get system status"""
        return {
            "phase": "4 - Presentation Layer",
            "llm_provider": self.llm_provider,
            "components": {
                "cli_interface": self.cli_interface is not None,
                "api_endpoints": self.api_endpoints is not None,
                "web_app": self.web_app is not None,
                "ui_components": True
            },
            "features": {
                "input_forms": True,
                "results_renderer": True,
                "api_endpoints": True,
                "web_ui": True,
                "cli_interface": True
            }
        }


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Phase 4 - Restaurant Recommendation Presentation Layer")
    parser.add_argument("--mode", choices=["cli", "api", "web"], default="web",
                       help="Run mode: cli (interactive), api (API server), web (web app)")
    parser.add_argument("--provider", default="groq", choices=["groq", "openai", "anthropic", "mock"],
                       help="LLM provider")
    parser.add_argument("--host", default="0.0.0.0", help="Host for API/web server")
    parser.add_argument("--port", type=int, default=5000, help="Port for API/web server")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    parser.add_argument("--status", action="store_true", help="Show system status")
    
    args = parser.parse_args()
    
    # Initialize integration
    integration = Phase4Integration(llm_provider=args.provider)
    
    if args.status:
        status = integration.get_system_status()
        print("📊 System Status:")
        print(f"  Phase: {status['phase']}")
        print(f"  LLM Provider: {status['llm_provider']}")
        print("  Components:")
        for component, active in status['components'].items():
            status_icon = "✅" if active else "❌"
            print(f"    {status_icon} {component}")
        print("  Features:")
        for feature, available in status['features'].items():
            feature_icon = "✅" if available else "❌"
            print(f"    {feature_icon} {feature}")
        return
    
    try:
        if args.mode == "cli":
            asyncio.run(integration.run_cli_demo())
        elif args.mode == "api":
            integration.run_api_server(host=args.host, port=args.port, debug=args.debug)
        elif args.mode == "web":
            integration.run_web_app(host=args.host, port=args.port, debug=args.debug)
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Error: {e}")
        if args.debug:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
