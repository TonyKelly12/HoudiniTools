"""
Main entry point for the ClickUp Task Manager
"""

import hou
from .clickup_task_manager_oauth import launch_task_manager, launch_pomodoro_timer

def main():
    """Main entry point for the ClickUp Task Manager"""
    try:
        task_manager = launch_task_manager()
        return task_manager
    except Exception as e:
        hou.ui.displayMessage(f"Error launching ClickUp Task Manager: {str(e)}", 
                            severity=hou.severityType.Error)
        return None

if __name__ == "__main__":
    main() 