import hou
from collections import defaultdict

# Access the current node
node = hou.pwd()
geo = node.geometry()


# Read parameters with safety
def safe_read(parm, default):
    """Safely read a parameter value"""
    try:
        if parm is None:
            return default

        value = parm.eval()
        if isinstance(value, tuple) and len(value) > 0:
            return value[0]
        return value
    except (hou.OperationFailed, AttributeError, TypeError):
        return default


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
        "align_axis", "Alignment Axis", ["X", "Y", "Z"], default_value=0
    )
    parm_group.addParmTemplate(axis_parm)

    # Set new parameter template
    node.setParmTemplateGroup(parm_group)

    # Use defaults for first run
    connection_prefix = "c"
    debug_mode = True
    align_axis = 0  # X axis
else:
    # Read parameters safely
    connection_prefix = safe_read(node.parm("connection_prefix"), "c")
    debug_mode = safe_read(node.parm("debug_mode"), True)
    align_axis = safe_read(node.parm("align_axis"), 0)


# Function to print debug info if enabled
def debug_print(*args, **kwargs):
    if debug_mode:
        print(*args, **kwargs)


# Get input geometries
input_geos = []
input_names = []

# Handle both tuple and integer returns from inputs()
inputs_obj = node.inputs()
if isinstance(inputs_obj, tuple):
    # Process tuple of nodes
    for input_node in inputs_obj:
        if input_node:
            try:
                input_geo = input_node.geometry()
                if input_geo:
                    input_geos.append(input_geo)
                    input_names.append(input_node.name())
            except (hou.OperationFailed, AttributeError):
                pass
else:
    # Process as integer
    try:
        num_inputs = int(inputs_obj)
        for i in range(num_inputs):
            input_node = node.input(i)
            if input_node:
                input_geo = input_node.geometry()
                if input_geo:
                    input_geos.append(input_geo)
                    input_names.append(input_node.name())
    except (hou.OperationFailed, AttributeError):
        pass

# Check if we have enough inputs
if len(input_geos) < 2:
    # Just merge whatever we have and exit
    for input_geo in input_geos:
        geo.merge(input_geo)
    debug_print("Need at least 2 inputs to perform alignment")
    exit()

debug_print(f"Found {len(input_geos)} input geometries")

# Analyze point groups in each input
for i, input_geo in enumerate(input_geos):
    groups = [g.name() for g in input_geo.pointGroups()]
    debug_print(f"Input {i} ({input_names[i]}): Groups: {groups}")

    # Filter for connection groups
    conn_groups = [g for g in groups if g.startswith(connection_prefix)]
    debug_print(f"  Connection groups: {conn_groups}")


# Function to get centroid of a group
def get_group_centroid(geometry, group_name):
    try:
        group = geometry.findPointGroup(group_name)
        if not group:
            return None

        points = list(group.points())
        if not points:
            return None

        centroid = hou.Vector3(0, 0, 0)
        for point in points:
            centroid += point.position()

        centroid /= len(points)
        return centroid
    except (hou.OperationFailed, AttributeError, ValueError):
        return None


# Find connections between parts
connections = defaultdict(list)

# For each geometry, find connection groups
for i, input_geo in enumerate(input_geos):
    for group in input_geo.pointGroups():
        group_name = group.name()
        if group_name.startswith(connection_prefix):
            # Store connection ID along with geo index and group name
            conn_id = group_name[len(connection_prefix):]
            connections[conn_id].append((i, group_name))
            debug_print(
                f"Found connection {conn_id} on input {i} with group {group_name}"
            )

# Order the parts for linear alignment
ordered_parts = []

# Start with the first object
if len(input_geos) > 0:
    ordered_parts.append(0)  # Start with the first object

    # For simplicity, we'll assume objects should be connected in sequence
    # (1 connects to 2, 2 connects to 3, etc.)
    # This is based on your screenshot showing a linear arrangement

    processed = set([0])  # Mark first object as processed

    # Find next connected part until all are processed
    while len(processed) < len(input_geos):
        # Find a connection from the last processed part to a new one
        last_part = ordered_parts[-1]
        next_part = None

        for conn_id, parts in connections.items():
            # Look for connections with the last part
            if any(idx == last_part for idx, _ in parts):
                # Find the other part in this connection
                for idx, _ in parts:
                    if idx != last_part and idx not in processed:
                        next_part = idx
                        ordered_parts.append(next_part)
                        processed.add(next_part)
                        debug_print(
                            f"Added part {next_part} to sequence after {last_part}"
                        )
                        break
                if next_part:
                    break

        # If no new connections found, try to find any unprocessed part
        if next_part is None:
            # If we can't find a connected part, just take the next unprocessed one
            for i in range(len(input_geos)):
                if i not in processed:
                    ordered_parts.append(i)
                    processed.add(i)
                    debug_print(f"Adding unconnected part {i} to sequence")
                    break

        # If we still can't find anything, we're done
        if len(ordered_parts) == len(processed) and len(processed) < len(input_geos):
            debug_print("Warning: Could not find connections for all parts")
            # Add any remaining parts
            for i in range(len(input_geos)):
                if i not in processed:
                    ordered_parts.append(i)
                    processed.add(i)
            break

debug_print(f"Ordered parts sequence: {ordered_parts}")

# Create transformed versions of the input geometries
transformed_geos = []

# Keep track of the current position along the chosen axis
current_position = 0.0

# Get axis index for positioning (0=X, 1=Y, 2=Z)
axis_idx = align_axis

# Process each part in order
for i, part_idx in enumerate(ordered_parts):
    input_geo = input_geos[part_idx]

    # Create a copy to transform
    transformed_geo = input_geo.freeze()

    if i > 0:  # Skip the first object (reference)
        # Get bounding box for current geometry
        bbox = transformed_geo.boundingBox()

        # Calculate how much to offset this part
        if i == 1:
            # For the first connection, measure from the start
            offset = current_position - bbox.minvec()[axis_idx]
        else:
            # For subsequent connections, align to current position
            offset = current_position - bbox.minvec()[axis_idx]

        # Apply translation
        translation = hou.Vector3(0, 0, 0)
        translation[axis_idx] = offset

        debug_print(f"Translating part {part_idx} by {translation}")

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
    debug_print(
        f"Part {part_idx} positioned at {current_position} along axis {axis_idx}"
    )

# Merge all transformed geometries into output
debug_print("Merging transformed geometries to output")
for transformed_geo in transformed_geos:
    geo.merge(transformed_geo)

debug_print("Alignment complete")
