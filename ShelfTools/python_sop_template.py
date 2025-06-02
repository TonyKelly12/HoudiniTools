import hou
import os
import sys

# Add scripts path
scripts_dir = os.path.join(hou.expandString("$HOME"), "scripts", "python")
if scripts_dir not in sys.path:
    sys.path.append(scripts_dir)

# Import simple_object_aligner module
try:
    import simple_object_aligner
except ImportError:
    print("ERROR: simple_object_aligner.py not found!")
    print(f"Make sure it exists in: {scripts_dir}")

    # Fall back to basic merge
    node = hou.pwd()
    geo = node.geometry()
    for i in range(len(node.inputs())):
        input_node = node.input(i)
        if input_node and input_node.geometry():
            geo.merge(input_node.geometry())
