"""
Groq API Setup and Test Script

Helps set up and test Groq API integration for Phase 4.
"""

import os
import sys
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def check_env_setup():
    """Check current environment setup"""
    print("🔍 Environment Setup Check")
    print("=" * 50)
    
    # Load environment variables
    load_dotenv()
    
    # Check for API key
    groq_api_key = os.getenv("GROQ_API_KEY")
    
    if groq_api_key:
        print(f"✅ GROQ_API_KEY found: {groq_api_key[:10]}...{groq_api_key[-4:]}")
        return True
    else:
        print("❌ GROQ_API_KEY not found in environment")
        return False

def show_env_file_status():
    """Show .env file status"""
    print("\n📁 .env File Status")
    print("=" * 50)
    
    env_file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
    
    if os.path.exists(env_file_path):
        print(f"✅ .env file exists: {env_file_path}")
        
        try:
            with open(env_file_path, 'r') as f:
                content = f.read()
                print(f"📄 File contents:")
                for line in content.split('\n'):
                    if line.strip():
                        if 'GROQ_API_KEY' in line:
                            # Mask the API key
                            if '=' in line:
                                key, value = line.split('=', 1)
                                if value.strip():
                                    masked_value = value[:10] + "..." + value[-4:] if len(value) > 14 else "***"
                                    print(f"   {key}={masked_value}")
                                else:
                                    print(f"   {key}=(empty)")
                        else:
                            print(f"   {line}")
        except Exception as e:
            print(f"❌ Error reading .env file: {e}")
    else:
        print(f"❌ .env file not found: {env_file_path}")
        print("💡 Creating .env file...")
        
        try:
            with open(env_file_path, 'w') as f:
                f.write("# Server\nPORT=3000\n\n")
                f.write("# LLM provider configuration\n")
                f.write("LLM_PROVIDER=groq\n")
                f.write("GROQ_API_KEY=your_groq_api_key_here\n")
                f.write("LLM_MODEL=llama3-8b-8192\n")
            print(f"✅ Created .env file with template")
        except Exception as e:
            print(f"❌ Error creating .env file: {e}")

def show_setup_instructions():
    """Show setup instructions"""
    print("\n📋 Setup Instructions")
    print("=" * 50)
    print("1. Get your Groq API key from: https://console.groq.com/keys")
    print("2. Add it to your .env file:")
    print("   GROQ_API_KEY=gsk_your_actual_api_key_here")
    print("3. Make sure the .env file is in the project root directory")
    print("4. Run this script again to verify the setup")

def test_groq_import():
    """Test Groq package import"""
    print("\n🧪 Groq Package Test")
    print("=" * 50)
    
    try:
        import groq
        print("✅ Groq package installed successfully")
        
        # Test client creation (without API key)
        try:
            from groq import Groq
            print("✅ Groq client import successful")
            return True
        except Exception as e:
            print(f"❌ Groq client import error: {e}")
            return False
            
    except ImportError:
        print("❌ Groq package not installed")
        print("💡 Install with: pip install groq")
        return False

def test_phase3_integration():
    """Test Phase 3 integration"""
    print("\n🔗 Phase 3 Integration Test")
    print("=" * 50)
    
    try:
        from phase3.llm_client import LLMClient
        from phase3.orchestrator import RecommendationOrchestrator
        print("✅ Phase 3 imports successful")
        
        # Test mock provider
        try:
            client = LLMClient(provider="mock")
            print("✅ Mock LLM client works")
            
            orchestrator = RecommendationOrchestrator(llm_provider="mock")
            print("✅ Mock orchestrator works")
            return True
        except Exception as e:
            print(f"❌ Mock client error: {e}")
            return False
            
    except ImportError as e:
        print(f"❌ Phase 3 import error: {e}")
        return False

def main():
    """Run setup check"""
    print("🚀 Groq API Setup Check for Phase 4")
    print("=" * 60)
    
    # Check environment
    env_ok = check_env_setup()
    
    # Show .env file status
    show_env_file_status()
    
    # Test Groq package
    groq_ok = test_groq_import()
    
    # Test Phase 3 integration
    phase3_ok = test_phase3_integration()
    
    # Show instructions if needed
    if not env_ok:
        show_setup_instructions()
    
    # Summary
    print("\n📊 Setup Summary")
    print("=" * 50)
    print(f"Environment: {'✅' if env_ok else '❌'}")
    print(f"Groq Package: {'✅' if groq_ok else '❌'}")
    print(f"Phase 3 Integration: {'✅' if phase3_ok else '❌'}")
    
    if env_ok and groq_ok and phase3_ok:
        print("\n🎉 Setup complete! Ready to test with real Groq API")
        print("💡 Run: python phase4/real_groq_test.py")
    else:
        print("\n⚠️  Setup incomplete. Please follow the instructions above.")

if __name__ == "__main__":
    main()
