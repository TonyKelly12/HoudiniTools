"""
Main entry point for the LLM Chat Interface
"""

import hou
from .claude_chat_ui import show_chat_ui

def main():
    """Main entry point for the LLM Chat Interface"""
    try:
        show_chat_ui()
    except Exception as e:
        hou.ui.displayMessage(f"Error launching LLM Chat Interface: {str(e)}", 
                            severity=hou.severityType.Error)

if __name__ == "__main__":
    main() 