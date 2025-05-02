import hou
import math
node = hou.pwd()
geo = node.geometry()

# Create parameters if they don't exist
if not node.parm("num_chairs"):
    parm_group = node.parmTemplateGroup()

    # Add num_chairs parameter
    num_chairs_parm = hou.IntParmTemplate(
        "num_chairs", "Number of Chairs", 1, default_value=(4,), min=1, max=12
    )
    parm_group.addParmTemplate(num_chairs_parm)

    # Add chair_inset parameter
    chair_inset_parm = hou.FloatParmTemplate(
        "chair_inset", "Chair Distance", 1, default_value=(0.8,), min=0.5, max=1.5
    )
    parm_group.addParmTemplate(chair_inset_parm)

    # Add table_scale parameter
    table_scale_parm = hou.FloatParmTemplate(
        "table_scale", "Table Scale", 1, default_value=(1.0,), min=0.1, max=5.0
    )
    parm_group.addParmTemplate(table_scale_parm)

    # Set the parameter template group
    node.setParmTemplateGroup(parm_group)

    # The node needs to be cooked again to use the new parameters
    # Use default values for this run
    num_chairs = 4
    chair_inset = 0.8
    table_scale = 1.0
else:
    # Parameters exist, get their values
    num_chairs = node.parm("num_chairs").eval()
    chair_inset = node.parm("chair_inset").eval()
    table_scale = node.parm("table_scale").eval()

# Get the input geometry (the circle)
input_geo = None
if len(node.inputs()) > 0 and node.inputs()[0]:
    input_geo = node.inputs()[0].geometry()

if not input_geo or len(input_geo.points()) == 0:
    # No valid input, create a default circle

    # Create a default circle with radius 1
    radius = 1.0
    center = hou.Vector3(0, 0, 0)

    # Add a message for the user
    node.addMessage(
        hou.severityType.Warning,
        "No valid input circle. Using default circle with radius 1.",
    )
else:
    # Calculate the circle center and radius
    circle_points = [point.position() for point in input_geo.points()]

    center = hou.Vector3(0, 0, 0)
    for point in circle_points:
        center += point
    center /= len(circle_points)

    # Calculate the radius (average distance from center to points)
    radius = 0
    for point in circle_points:
        radius += (point - center).length()
    radius /= len(circle_points)

# Create a point for the table at the center
table_point = geo.createPoint()
table_point.setPosition(center)

# Add attribute to identify this as a table point
if not geo.findPointAttrib("furniture_type"):
    furniture_type_attrib = geo.addAttrib(hou.attribType.Point, "furniture_type", "")
table_point.setAttribValue("furniture_type", "table")

# Add a scale attribute
if not geo.findPointAttrib("scale"):
    scale_attrib = geo.addAttrib(hou.attribType.Point, "scale", 0.0)
table_point.setAttribValue("scale", table_scale)
# Add chairs around the circle
for i in range(num_chairs):
    angle = 2 * math.pi * i / num_chairs

    # Calculate chair position on the circle
    chair_radius = radius * chair_inset
    chair_pos = hou.Vector3(
        center[0] + chair_radius * math.cos(angle),
        center[1],
        center[2] + chair_radius * math.sin(angle),
    )

    # Create chair point
    chair_point = geo.createPoint()
    chair_point.setPosition(chair_pos)
    chair_point.setAttribValue("furniture_type", "chair")
    chair_point.setAttribValue(
        "scale", table_scale * 0.6
    )  # Make chairs a bit smaller than table

    # Add rotation attribute to make chairs face the table
    if not geo.findPointAttrib("rotation"):
        rotation_attrib = geo.addAttrib(hou.attribType.Point, "rotation", 0.0)
    chair_point.setAttribValue("rotation", math.degrees(angle) + 180)
