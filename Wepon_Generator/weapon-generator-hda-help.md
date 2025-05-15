= Weapon Generator =

#icon: SHELF_weapon_generator
#context: obj
#internal: weapon_generator
#tags: weapons, generator, models

"""Generates assembled weapons from online parts library using the 3D Weapon Assembly API."""

= Overview =

This HDA allows you to browse and select weapon parts from an online parts library,
visualize them in the interface, and then assemble them into a complete weapon.

The tool connects to a 3D Weapon Assembly API server that hosts a variety of weapon types
and parts, downloads the selected parts, and automatically assembles them based on their
metadata.

@parameters
    API URL:
        URL of the 3D Weapon Assembly API server.
    Output Path:
        Directory where assembled weapons will be saved.

@related
    - File node
    - Merge node
    - Null node
    - Transform node

= Using the Weapon Generator =

This HDA provides an interactive interface to create weapons:

# Select the Weapon Type from the dropdown at the top. This will load the appropriate parts categories.
# Browse through available parts in each category using the up/down navigation buttons.
# The categories shown will vary based on the selected weapon type (e.g., swords will show blade, handle, guard, etc.)
# Click "Generate Weapon" when you're satisfied with your selection.
# The tool will download the selected parts from the API and assemble them into a complete weapon.
# The assembled weapon will be available through the OUTPUT connector of the node.

= Tips =
    
* The API URL can be changed if you're running the API server on a different machine or port.
* For best results, ensure your API server contains a variety of parts for each weapon type.
* Parts are automatically positioned based on their metadata, but you may need to adjust positions in some cases.
* You can modify the assembled weapon by connecting to other nodes or editing the generated nodes.

= Technical Details =

The Weapon Generator interfaces with a FastAPI backend that provides access to 3D models, textures,
and assembly metadata. The weapon assembly process happens in these steps:

# Selection of parts through the UI
# API retrieval of model files with proper metadata
# Import of model files into Houdini
# Transformation and assembly based on position data
# Output of the complete assembled model

The HDA creates a node network that includes File nodes for each part and Transform nodes to position them
correctly. All parts are merged into a single output.