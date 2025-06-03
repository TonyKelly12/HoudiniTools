"""
Redshift Material Tool Main
-------------------------
Entry point for the Redshift Material Tool.
"""

import hou
from .material_tool_dialog import RedshiftMaterialToolDialog


def create_redshift_material_tool_v2():
    """Launch the Redshift Material Tool dialog"""
    dialog = RedshiftMaterialToolDialog(hou.qt.mainWindow())
    dialog.show() 