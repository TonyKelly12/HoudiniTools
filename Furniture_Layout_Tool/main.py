"""
Main entry point for the Furniture Layout Tool
"""

import hou
from .furniture_layout_tool import create_table_chairs_ui, add_to_shelf

def main():
    """Main entry point for the Furniture Layout Tool"""
    try:
        create_table_chairs_ui()
    except Exception as e:
        hou.ui.displayMessage(f"Error launching Furniture Layout Tool: {str(e)}", 
                            severity=hou.severityType.Error)

if __name__ == "__main__":
    main() 