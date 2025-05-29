"""
Civilization Aware Weapon Generator
--------------------------------
Generates weapons based on civilization context and available assets.
"""

import hou
from typing import Dict, List


class CivilizationAwareWeaponGenerator:
    """Generates weapons based on civilization context"""

    def __init__(self):
        """Initialize the generator"""
        self.context = None

    def get_civilization_context(self, civilization_id: str) -> Dict:
        """Get the context for a specific civilization"""
        # TODO: Implement civilization context retrieval
        # For now, return a mock context
        return {
            "id": civilization_id,
            "name": "Test Civilization",
            "era": "medieval",
            "technology_level": "iron_age",
            "preferred_weapons": ["sword", "bow", "spear"],
            "material_preferences": {
                "primary": "iron",
                "secondary": "wood",
                "decorative": "gold"
            }
        }

    def get_filtered_weapons(self, context: Dict) -> List[Dict]:
        """Get weapons filtered by civilization context"""
        # TODO: Implement weapon filtering based on context
        # For now, return mock weapons
        return [
            {
                "id": "sword_1",
                "type": "sword",
                "name": "Iron Longsword",
                "materials": ["iron", "wood", "leather"],
                "era": "medieval",
                "technology_level": "iron_age"
            },
            {
                "id": "bow_1",
                "type": "bow",
                "name": "Composite Bow",
                "materials": ["wood", "sinew", "horn"],
                "era": "medieval",
                "technology_level": "iron_age"
            }
        ]

    def setup_houdini_parameters(self, context: Dict):
        """Set up Houdini parameters based on civilization context"""
        # Get or create the weapon generator node
        parent = hou.node("/obj")
        weapon_node = parent.node("weapon_generator")
        if not weapon_node:
            weapon_node = parent.createNode("geo", "weapon_generator")

        # Create parameters
        parm_group = weapon_node.parmTemplateGroup()
        
        # Civilization parameters
        civ_folder = hou.FolderParmTemplate("civilization", "Civilization")
        civ_folder.addParmTemplate(
            hou.StringParmTemplate("civ_id", "Civilization ID", 1)
        )
        civ_folder.addParmTemplate(
            hou.StringParmTemplate("civ_name", "Civilization Name", 1)
        )
        civ_folder.addParmTemplate(
            hou.StringParmTemplate("civ_era", "Era", 1)
        )
        civ_folder.addParmTemplate(
            hou.StringParmTemplate("tech_level", "Technology Level", 1)
        )
        parm_group.append(civ_folder)

        # Weapon parameters
        weapon_folder = hou.FolderParmTemplate("weapon", "Weapon")
        weapon_folder.addParmTemplate(
            hou.StringParmTemplate("weapon_type", "Type", 1)
        )
        weapon_folder.addParmTemplate(
            hou.StringParmTemplate("weapon_name", "Name", 1)
        )
        weapon_folder.addParmTemplate(
            hou.StringParmTemplate("materials", "Materials", 3)
        )
        parm_group.append(weapon_folder)

        # Apply the parameter template
        weapon_node.setParmTemplateGroup(parm_group)

        # Set parameter values from context
        weapon_node.parm("civ_id").set(context["id"])
        weapon_node.parm("civ_name").set(context["name"])
        weapon_node.parm("civ_era").set(context["era"])
        weapon_node.parm("tech_level").set(context["technology_level"])

    def generate_civilization_weapon(self):
        """Generate a weapon based on civilization context"""
        # Get the weapon generator node
        weapon_node = hou.node("/obj/weapon_generator")
        if not weapon_node:
            raise RuntimeError("Weapon generator node not found")

        # Get civilization context
        civ_id = weapon_node.parm("civ_id").eval()
        context = self.get_civilization_context(civ_id)

        # Get filtered weapons
        weapons = self.get_filtered_weapons(context)
        if not weapons:
            raise RuntimeError("No suitable weapons found for civilization")

        # Select a weapon (for now, just use the first one)
        selected_weapon = weapons[0]

        # Set weapon parameters
        weapon_node.parm("weapon_type").set(selected_weapon["type"])
        weapon_node.parm("weapon_name").set(selected_weapon["name"])
        for i, material in enumerate(selected_weapon["materials"]):
            weapon_node.parm(f"materials{i}").set(material)

        # Build the weapon
        self.build_weapon_from_assets(weapons, context)

    def build_weapon_from_assets(self, weapons: List[Dict], context: Dict):
        """Build the weapon using available assets"""
        # Get the weapon generator node
        weapon_node = hou.node("/obj/weapon_generator")
        if not weapon_node:
            raise RuntimeError("Weapon generator node not found")

        # Create a new geometry node for the weapon
        weapon_geo = weapon_node.createNode("geo", "weapon_assembly")

        # TODO: Implement actual weapon building logic
        # For now, just create a placeholder
        box = weapon_geo.createNode("box")
        box.parm("size").set(1)
        box.parm("center").set(0)

        # Layout the nodes
        weapon_geo.layoutChildren()

    def generate_default_weapon(self):
        """Generate a default weapon when no civilization context is available"""
        # Create a basic weapon node
        parent = hou.node("/obj")
        weapon_node = parent.createNode("geo", "default_weapon")

        # Create a simple weapon shape
        box = weapon_node.createNode("box")
        box.parm("size").set(1)
        box.parm("center").set(0)

        # Layout the nodes
        weapon_node.layoutChildren() 