#!/usr/bin/env python3
"""
Quick start script for Confluence AI Assistant.
"""

import sys
import subprocess
import os
from pathlib import Path

def check_requirements():
    """Check if requirements are installed."""
    try:
        import streamlit
        import openai
        import requests
        from dotenv import load_dotenv
        return True
    except ImportError:
        return False

def install_requirements():
    """Install requirements."""
    print("Installing requirements...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        return True
    except subprocess.CalledProcessError:
        return False

def check_env_file():
    """Check if .env file exists."""
    return os.path.exists(".env")

def create_env_file():
    """Create .env file from template."""
    if os.path.exists("env.example"):
        with open("env.example", "r") as src:
            content = src.read()
        with open(".env", "w") as dst:
            dst.write(content)
        return True
    return False

def main():
    """Main function."""
    print("🚀 Confluence AI Assistant - Quick Start")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not os.path.exists("requirements.txt"):
        print("❌ Please run this script from the project directory")
        sys.exit(1)
    
    # Check requirements
    if not check_requirements():
        print("📦 Installing requirements...")
        if not install_requirements():
            print("❌ Failed to install requirements")
            sys.exit(1)
        print("✅ Requirements installed successfully")
    else:
        print("✅ Requirements already installed")
    
    # Check .env file
    if not check_env_file():
        print("📝 Creating .env file from template...")
        if create_env_file():
            print("✅ .env file created")
            print("⚠️  Please edit .env file with your credentials before running the app")
        else:
            print("❌ Failed to create .env file")
            sys.exit(1)
    else:
        print("✅ .env file found")
    
    # Check if credentials are configured
    from dotenv import load_dotenv
    load_dotenv()
    
    required_vars = ['CONFLUENCE_URL', 'CONFLUENCE_USERNAME', 'CONFLUENCE_API_TOKEN', 'OPENAI_API_KEY']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"⚠️  Missing environment variables: {', '.join(missing_vars)}")
        print("Please edit .env file with your credentials")
        return
    
    # Ask user what they want to do
    print("\nWhat would you like to do?")
    print("1. Start web interface (Streamlit)")
    print("2. Start CLI interactive mode")
    print("3. Exit")
    
    choice = input("\nEnter your choice (1-4): ").strip()
    
    if choice == "1":
        print("\n🌐 Starting web interface...")
        subprocess.run([sys.executable, "-m", "streamlit", "run", "app.py"])
    elif choice == "2":
        print("\n💻 Starting CLI interactive mode...")
        subprocess.run([sys.executable, "cli.py", "--interactive"])
    elif choice == "3":
        print("Goodbye!")
    else:
        print("Invalid choice. Please run the script again.")

if __name__ == "__main__":
    main()
