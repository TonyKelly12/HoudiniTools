"""
Weapon Generator Package
-----------------------
A Houdini tool for generating and customizing weapons with civilization-aware features.
"""

__version__ = "1.0.0"

from .ui.weapon_generator_widget import WeaponGeneratorWidget
from .ui.weapon_part_upload_widget import WeaponPartUploadWidget
from .core.civilization_aware_generator import CivilizationAwareWeaponGenerator

__all__ = [
    'WeaponGeneratorWidget',
    'WeaponPartUploadWidget',
    'CivilizationAwareWeaponGenerator'
] 