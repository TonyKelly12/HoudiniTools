"""
Parameter definition for the Weapon Generator HDA.
This creates all the parameters and UI elements needed for the tool.
"""

import hou


def create_parameters():
    """Create Weapon Generator parameters"""

    # Get the node
    node = hou.pwd()
    ptg = node.parmTemplateGroup()

    # Create folder tabs
    api_folder = hou.FolderParmTemplate(
        "api_folder", "API Settings", folder_type=hou.folderType.Tabs
    )
    parts_folder = hou.FolderParmTemplate(
        "parts_folder", "Weapon Parts", folder_type=hou.folderType.Tabs
    )
    generation_folder = hou.FolderParmTemplate(
        "generation_folder", "Generation", folder_type=hou.folderType.Tabs
    )

    # API Settings
    api_url = hou.StringParmTemplate(
        "api_url", "API URL", 1, default_value=["http://localhost:8000"]
    )
    api_folder.addParmTemplate(api_url)

    # Weapon type
    weapon_types = [
        "sword",
        "axe",
        "mace",
        "bow",
        "spear",
        "dagger",
        "staff",
        "shield",
        "gun",
        "rifle",
        "custom",
    ]
    weapon_type = hou.MenuParmTemplate(
        "weapon_type", "Weapon Type", weapon_types, default_value=0
    )
    weapon_type.setScriptCallback("hou.phm().updatePartTypes()")
    weapon_type.setScriptCallbackLanguage(hou.scriptLanguage.Python)
    parts_folder.addParmTemplate(weapon_type)

    # Part Browser button
    browse_divider = hou.LabelParmTemplate("browse_divider", "")
    parts_folder.addParmTemplate(browse_divider)

    browse_button = hou.ButtonParmTemplate("open_browser", "Open Part Browser")
    browse_button.setScriptCallback("hou.phm().openPartBrowser(kwargs)")
    browse_button.setScriptCallbackLanguage(hou.scriptLanguage.Python)
    parts_folder.addParmTemplate(browse_button)

    parts_divider = hou.LabelParmTemplate("parts_divider", "Select Individual Parts")
    parts_folder.addParmTemplate(parts_divider)

    # Parts - up to 10 supported
    for i in range(10):
        part_folder = hou.FolderParmTemplate(
            f"part_{i}_folder", f"Part {i+1}", folder_type=hou.folderType.Collapsible
        )

        # Part type menu - initially empty, will be populated by script
        part_type = hou.MenuParmTemplate(
            f"part_{i}_type", "Part Type", ["handle", "blade"], default_value=0
        )
        part_folder.addParmTemplate(part_type)

        # Part model file
        part_model = hou.StringParmTemplate(f"part_{i}_model", "Model File", 1)
        part_folder.addParmTemplate(part_model)

        # Browse button
        browse_part = hou.ButtonParmTemplate(f"browse_part_{i}", "Browse...")
        browse_part.setScriptCallback("hou.phm().browsePartFile(kwargs)")
        browse_part.setScriptCallbackLanguage(hou.scriptLanguage.Python)
        browse_part.setTags({"parm_name": f"part_{i}_model"})
        part_folder.addParmTemplate(browse_part)

        # Add the part folder to the parts tab
        parts_folder.addParmTemplate(part_folder)

    # Generation options
    align_axis = hou.MenuParmTemplate(
        "align_axis", "Alignment Axis", ["X", "Y", "Z"], default_value=1
    )
    generation_folder.addParmTemplate(align_axis)

    spacing = hou.FloatParmTemplate(
        "spacing", "Part Spacing", 1, default_value=[0.1], min=0.0, max=10.0
    )
    generation_folder.addParmTemplate(spacing)

    auto_center = hou.ToggleParmTemplate(
        "auto_center", "Auto Center Result", default_value=True
    )
    generation_folder.addParmTemplate(auto_center)

    generate_button = hou.ButtonParmTemplate("generate", "Generate Weapon")
    generate_button.setScriptCallback("hou.phm().generateWeapon(kwargs)")
    generate_button.setScriptCallbackLanguage(hou.scriptLanguage.Python)
    generation_folder.addParmTemplate(generate_button)

    # Hidden parameters for script execution
    weapon_script = hou.StringParmTemplate("weapon_script", "Weapon Script", 1)
    weapon_script.setDefaultValue([""])
    weapon_script.setVisible(False)

    # Add all folders to the parameter template group
    ptg.addParmTemplate(api_folder)
    ptg.addParmTemplate(parts_folder)
    ptg.addParmTemplate(generation_folder)
    ptg.addParmTemplate(weapon_script)

    # Set the parameter template group on the node
    node.setParmTemplateGroup(ptg)


# Call the function to create parameters
create_parameters()
