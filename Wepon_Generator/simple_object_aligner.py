import hou

# Access the current node
node = hou.pwd()
geo = node.geometry()

# Create parameters if they don't exist
if not node.parm("connection_prefix"):
    parm_group = node.parmTemplateGroup()

    # Connection prefix
    prefix_parm = hou.StringParmTemplate(
        "connection_prefix", "Connection Group Prefix", 1, default_value=("c",)
    )
    parm_group.addParmTemplate(prefix_parm)

    # Debug mode
    debug_parm = hou.ToggleParmTemplate("debug_mode", "Debug Mode", default_value=True)
    parm_group.addParmTemplate(debug_parm)

    # Axis selection for alignment
    axis_parm = hou.MenuParmTemplate(
        "align_axis", "Alignment Axis", ["X", "Y", "Z"], default_value=1  # Default to Y
    )
    parm_group.addParmTemplate(axis_parm)

    # Set the parameter template group
    node.setParmTemplateGroup(parm_group)

    # Use defaults for first run
    connection_prefix = "c"
    debug_mode = True
    align_axis = 2  # Y axis
else:
    # Read parameters
    connection_prefix = node.parm("connection_prefix").evalAsString()
    debug_mode = node.parm("debug_mode").eval()
    align_axis = node.parm("align_axis").eval()


# Function to print debug info if enabled
def debug_print(*args, **kwargs):
    if debug_mode:
        print(*args, **kwargs)


# Get input geometries
input_geos = []
input_nodes = []

# Get all input connections
num_inputs = len(node.inputs())
debug_print(f"Node has {num_inputs} inputs")

for i in range(num_inputs):
    input_node = node.input(i)
    if input_node:
        try:
            input_geo = input_node.geometry()
            if input_geo:
                input_geos.append(input_geo)
                input_nodes.append(input_node)
                debug_print(f"Input {i}: {input_node.name()}")
        except (hou.OperationFailed, AttributeError) as e:
            debug_print(f"Error getting geometry from input {i}: {e}")

# Check if we have enough inputs
if len(input_geos) < 1:
    debug_print("No valid inputs found")
    exit()
elif len(input_geos) == 1:
    # Just one input, copy it and exit
    geo.merge(input_geos[0])
    debug_print("Only one input, merged without modification")
    exit()

debug_print(f"Processing {len(input_geos)} input geometries")

# Try to determine part types from node names or comments
weapon_parts = []
for i, input_node in enumerate(input_nodes):
    # Get the node name for possible part identification
    node_name = input_node.name().lower()
    part_type = "unknown"

    # Try to identify part type from node name
    if "blade" in node_name:
        part_type = "blade"
    elif "handle" in node_name or "grip" in node_name:
        part_type = "handle"
    elif "guard" in node_name:
        part_type = "guard"
    elif "pommel" in node_name:
        part_type = "pommel"

    # Also check node comment
    comment = input_node.comment()
    if comment:
        if "blade" in comment.lower():
            part_type = "blade"
        elif "handle" in comment.lower() or "grip" in comment.lower():
            part_type = "handle"
        elif "guard" in comment.lower():
            part_type = "guard"
        elif "pommel" in comment.lower():
            part_type = "pommel"

    weapon_parts.append({"index": i, "type": part_type, "geo": input_geos[i]})

# Simple preferred order for parts: handle -> guard -> blade -> pommel (special case)
part_order = {
    "handle": 0,
    "grip": 0,  # Same as handle
    "guard": 1,
    "blade": 2,
    "pommel": 3,  # Special case
}

# Sort parts based on preferred order
sorted_parts = sorted(weapon_parts, key=lambda p: part_order.get(p["type"], 999))

debug_print("Sorted parts:")
for part in sorted_parts:
    debug_print(f"  {part['type']} (index: {part['index']})")

# Create transformed versions of the input geometries
transformed_geos = []

# Keep track of the current position along the chosen axis
current_position = 0.0

# Get axis index for positioning (0=X, 1=Y, 2=Z)
axis_idx = align_axis

# Process each part in order
for i, part in enumerate(sorted_parts):
    input_geo = part["geo"]
    part_type = part["type"]

    # Create a copy to transform
    transformed_geo = input_geo.freeze()

    if i > 0:  # Skip the first object (reference)
        # Get bounding box for current geometry
        bbox = transformed_geo.boundingBox()

        # Calculate how much to offset this part
        if part_type == "pommel" and i > 0:
            # Special case: pommel goes at bottom of handle
            # Find min instead of max
            offset = -bbox.maxvec()[axis_idx]
        else:
            # Normal case: stack from bottom to top
            offset = current_position - bbox.minvec()[axis_idx]

        # Apply translation
        translation = hou.Vector3(0, 0, 0)
        translation[axis_idx] = offset

        debug_print(f"Translating {part_type} by {translation}")

        # Apply translation to all points
        for point in transformed_geo.points():
            point.setPosition(point.position() + translation)

        # Update current position to the end of this object
        bbox = transformed_geo.boundingBox()  # Get new bounding box after translation
        current_position = bbox.maxvec()[axis_idx]
    else:
        # For the first object, just get its max position for the next object
        bbox = transformed_geo.boundingBox()
        current_position = bbox.maxvec()[axis_idx]

    transformed_geos.append(transformed_geo)

# Merge all transformed geometries into output
debug_print("Merging transformed geometries to output")
for transformed_geo in transformed_geos:
    geo.merge(transformed_geo)

debug_print("Alignment complete")
