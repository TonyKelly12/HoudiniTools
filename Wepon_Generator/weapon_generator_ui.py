"""
Weapon Generator UI for Houdini
-------------------------------
This module provides a UI for the Weapon Generator HDA, allowing users to
browse and select weapon parts from an online parts library.
"""

import hou
from PySide2 import QtWidgets
import requests

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


class WeaponAssemblyAPI:
    def __init__(self, base_url="http://localhost:8003"):
        self.base_url = base_url
        self.headers = {"Content-Type": "application/json", "Accept": "application/json"}

    def create_assembly(self, assembly_data):
        try:
            url = f"{self.base_url}/assemblies"
            response = requests.post(url, json=assembly_data, headers=self.headers)
            if response.status_code == 200:
                return response.json()
            else:
                print(f"API Error ({response.status_code}): {response.text}")
                return None
        except Exception as e:
            print(f"Error creating assembly: {str(e)}")
            return None
    
    