"""
Weapon Generator UI for Houdini
-------------------------------
This module provides a UI for the Weapon Generator HDA, allowing users to
browse and select weapon parts from an online parts library.
"""

import hou
from PySide2 import QtWidgets

from .api.weapon_assembly_api import WeaponAssemblyAPI
from .ui.weapon_part_upload_widget import WeaponPartUploadWidget
from .core.civilization_aware_generator import CivilizationAwareWeaponGenerator


def show_weapon_part_upload():
    """Show the weapon part upload UI"""
    dialog = QtWidgets.QDialog(hou.ui.mainQtWindow())
    dialog.setWindowTitle("Upload Weapon Part")
    dialog.setMinimumSize(600, 400)

    layout = QtWidgets.QVBoxLayout()
    widget = WeaponPartUploadWidget(dialog, WeaponAssemblyAPI())
    layout.addWidget(widget)
    dialog.setLayout(layout)

    dialog.show()


def generate_civilization_weapon(civilization_id: str):
    """Generate a weapon based on civilization context"""
    generator = CivilizationAwareWeaponGenerator()
    context = generator.get_civilization_context(civilization_id)
    generator.setup_houdini_parameters(context)
    generator.generate_civilization_weapon()


def generate_default_weapon():
    """Generate a default weapon"""
    generator = CivilizationAwareWeaponGenerator()
    generator.generate_default_weapon()
