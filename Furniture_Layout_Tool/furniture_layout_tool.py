import hou
import math
import numpy as np

class FurnitureLayoutTool:
    def __init__(self):
        self.table_model_path = ""
        self.chair_model_path = ""
        
    def set_furniture_models(self, table_path, chair_path):
        """Set the paths to the furniture models"""
        self.table_model_path = table_path
        self.chair_model_path = chair_path
    
    def create_table_chairs_from_circle(self, circle_node, num_chairs=4, chair_inset=0.8):
        """
        Create a table and chairs based on a circle node
        
        Args:
            circle_node: The circle node to use as a guide
            num_chairs: Number of chairs to place around the table
            chair_inset: How close the chairs are to the table (0-1)
        """
        # Get the circle's transform information
        circle_xform = circle_node.worldTransform()
        circle_pos = circle_node.worldPosition()
        circle_rot = circle_node.worldTransform().extractRotates()
        
        # Get the circle's scale to determine table size
        # Using the X scale as the circle radius
        circle_scale = circle_node.worldTransform().extractScales()
        table_radius = circle_scale[0]
        
        # Create furniture container
        furniture_container = hou.node("/obj").createNode("geo", "table_and_chairs")
        
        # Create table at center of circle
        table = self._create_furniture_instance(
            furniture_container, 
            "table", 
            self.table_model_path, 
            circle_pos, 
            circle_rot, 
            [table_radius*0.8, table_radius*0.8, table_radius*0.8]  # Scale table to 80% of circle
        )
        
        # Create chairs around the circle
        chair_points = []
        for i in range(num_chairs):
            angle = 2 * math.pi * i / num_chairs
            
            # Calculate chair position on the circle
            chair_radius = table_radius * chair_inset
            chair_x = circle_pos[0] + chair_radius * math.cos(angle)
            chair_y = circle_pos[1]
            chair_z = circle_pos[2] + chair_radius * math.sin(angle)
            chair_pos = [chair_x, chair_y, chair_z]
            
            # Chair rotation - facing the center of the table
            chair_rot = [0, math.degrees(angle) + 180, 0]  # Add circle rotation
            
            # Create chair instance
            chair = self._create_furniture_instance(
                furniture_container, 
                f"chair_{i+1}", 
                self.chair_model_path, 
                chair_pos, 
                chair_rot, 
                [0.6, 0.6, 0.6]  # Scale chairs to 60% of table
            )
            
            chair_points.append(chair_pos)
        
        # Organize the network
        furniture_container.layoutChildren()
        
        return furniture_container
    
    def _create_furniture_instance(self, parent_node, name, model_path, position, rotation, scale):
        """Helper to create a furniture instance"""
        # Create object merge for the model
        obj_merge = parent_node.createNode("object_merge", name)
        obj_merge.parm("objpath1").set(model_path)
        
        # Add transform to position, rotate and scale
        transform = parent_node.createNode("xform", f"{name}_xform")
        transform.setInput(0, obj_merge)
        
        # Set position
        transform.parm("tx").set(position[0])
        transform.parm("ty").set(position[1])
        transform.parm("tz").set(position[2])
        
        # Set rotation
        transform.parm("rx").set(rotation[0])
        transform.parm("ry").set(rotation[1])
        transform.parm("rz").set(rotation[2])
        
        # Set scale
        transform.parm("sx").set(scale[0])
        transform.parm("sy").set(scale[1])
        transform.parm("sz").set(scale[2])
        
        return transform
    
    def project_furniture_to_surface(self, furniture_container, surface_node, height_offset=0):
        """Project furniture points onto a surface"""
        if not surface_node:
            return
        
        # Create a ray SOP to project points onto the surface
        ray_node = furniture_container.createNode("ray", "project_to_surface")
        
        # Set up the ray parameters
        ray_node.parm("group").set("*")  # Project all points
        ray_node.parm("dirx").set(0)
        ray_node.parm("diry").set(-1)  # Project down
        ray_node.parm("dirz").set(0)
        
        # Connect the surface geometry
        object_merge = furniture_container.createNode("object_merge", "surface_ref")
        object_merge.parm("objpath1").set(surface_node.path())
        ray_node.setInput(1, object_merge)
        
        # Find all transform nodes
        xform_nodes = [node for node in furniture_container.children() 
                      if node.type().name() == "xform"]
        
        # Create null to merge all furniture
        merge_node = furniture_container.createNode("merge", "furniture_merge")
        
        # Connect all xform nodes
        for i, xform in enumerate(xform_nodes):
            merge_node.setInput(i, xform)
        
        # Connect to ray node
        ray_node.setInput(0, merge_node)
        
        # Apply height offset if needed
        if height_offset != 0:
            offset_node = furniture_container.createNode("attribadjust", "height_offset")
            offset_node.setInput(0, ray_node)
            offset_node.parm("adjustpositions").set(1)
            offset_node.parm("adjust_py").set(height_offset)
            
            final_node = offset_node
        else:
            final_node = ray_node
        
        # Create null output
        output = furniture_container.createNode("null", "OUTPUT")
        output.setInput(0, final_node)
        
        # Set display flags
        output.setDisplayFlag(True)
        output.setRenderFlag(True)
        
        furniture_container.layoutChildren()
        
        return furniture_container

def create_table_chairs_ui():
    """User interface for the tool"""
    import hou
    from PySide2 import QtWidgets, QtCore
    
    # Create dialog
    dialog = QtWidgets.QDialog(hou.ui.mainQtWindow())
    dialog.setWindowTitle("Table & Chairs Layout Tool")
    dialog.setMinimumWidth(400)
    
    layout = QtWidgets.QVBoxLayout()
    dialog.setLayout(layout)
    
    # Circle node selection
    circle_layout = QtWidgets.QHBoxLayout()
    circle_label = QtWidgets.QLabel("Circle Node:")
    circle_input = QtWidgets.QLineEdit()
    circle_button = QtWidgets.QPushButton("...")
    
    circle_layout.addWidget(circle_label)
    circle_layout.addWidget(circle_input)
    circle_layout.addWidget(circle_button)
    layout.addLayout(circle_layout)
    
    # Surface selection for projection (optional)
    surface_layout = QtWidgets.QHBoxLayout()
    surface_label = QtWidgets.QLabel("Project to Surface (Optional):")
    surface_input = QtWidgets.QLineEdit()
    surface_button = QtWidgets.QPushButton("...")
    
    surface_layout.addWidget(surface_label)
    surface_layout.addWidget(surface_input)
    surface_layout.addWidget(surface_button)
    layout.addLayout(surface_layout)
    
    # Table model selection
    table_layout = QtWidgets.QHBoxLayout()
    table_label = QtWidgets.QLabel("Table Model:")
    table_input = QtWidgets.QLineEdit()
    table_button = QtWidgets.QPushButton("...")
    
    table_layout.addWidget(table_label)
    table_layout.addWidget(table_input)
    table_layout.addWidget(table_button)
    layout.addLayout(table_layout)
    
    # Chair model selection
    chair_layout = QtWidgets.QHBoxLayout()
    chair_label = QtWidgets.QLabel("Chair Model:")
    chair_input = QtWidgets.QLineEdit()
    chair_button = QtWidgets.QPushButton("...")
    
    chair_layout.addWidget(chair_label)
    chair_layout.addWidget(chair_input)
    chair_layout.addWidget(chair_button)
    layout.addLayout(chair_layout)
    
    # Number of chairs slider
    num_chairs_layout = QtWidgets.QHBoxLayout()
    num_chairs_label = QtWidgets.QLabel("Number of Chairs:")
    num_chairs_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
    num_chairs_slider.setMinimum(1)
    num_chairs_slider.setMaximum(8)
    num_chairs_slider.setValue(4)
    num_chairs_value = QtWidgets.QLabel("4")
    
    num_chairs_layout.addWidget(num_chairs_label)
    num_chairs_layout.addWidget(num_chairs_slider)
    num_chairs_layout.addWidget(num_chairs_value)
    layout.addLayout(num_chairs_layout)
    
    # Chair inset slider
    chair_inset_layout = QtWidgets.QHBoxLayout()
    chair_inset_label = QtWidgets.QLabel("Chair Distance:")
    chair_inset_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
    chair_inset_slider.setMinimum(50)
    chair_inset_slider.setMaximum(150)
    chair_inset_slider.setValue(80)
    chair_inset_value = QtWidgets.QLabel("0.8")
    
    chair_inset_layout.addWidget(chair_inset_label)
    chair_inset_layout.addWidget(chair_inset_slider)
    chair_inset_layout.addWidget(chair_inset_value)
    layout.addLayout(chair_inset_layout)
    
    # Height offset
    height_layout = QtWidgets.QHBoxLayout()
    height_label = QtWidgets.QLabel("Height Offset:")
    height_input = QtWidgets.QDoubleSpinBox()
    height_input.setRange(-10, 10)
    height_input.setValue(0)
    height_input.setSingleStep(0.1)
    
    height_layout.addWidget(height_label)
    height_layout.addWidget(height_input)
    layout.addLayout(height_layout)
    
    # Create button
    create_button = QtWidgets.QPushButton("Create Table & Chairs")
    layout.addWidget(create_button)
    
    # Connect signals
    def on_circle_button_clicked():
        node = hou.ui.selectNode(title="Select Circle Node")
        if node:
            circle_input.setText(node)
    
    def on_surface_button_clicked():
        node = hou.ui.selectNode(title="Select Surface Node")
        if node:
            surface_input.setText(node)
    
    def on_table_button_clicked():
        node = hou.ui.selectNode(title="Select Table Model")
        if node:
            table_input.setText(node)
    
    def on_chair_button_clicked():
        node = hou.ui.selectNode(title="Select Chair Model")
        if node:
            chair_input.setText(node)
    
    def on_num_chairs_changed(value):
        num_chairs_value.setText(str(value))
    
    def on_chair_inset_changed(value):
        chair_inset_value.setText(str(value/100.0))
    
    def on_create_clicked():
        circle_path = circle_input.text()
        surface_path = surface_input.text()
        table_path = table_input.text()
        chair_path = chair_input.text()
        num_chairs = num_chairs_slider.value()
        chair_inset = chair_inset_slider.value() / 100.0
        height_offset = height_input.value()
        
        # Validate inputs
        if not circle_path:
            QtWidgets.QMessageBox.warning(dialog, "Error", "Please select a circle node")
            return
        
        if not table_path:
            QtWidgets.QMessageBox.warning(dialog, "Error", "Please select a table model")
            return
        
        if not chair_path:
            QtWidgets.QMessageBox.warning(dialog, "Error", "Please select a chair model")
            return
        
        # Get nodes
        circle_node = hou.node(circle_path)
        surface_node = hou.node(surface_path) if surface_path else None
        
        # Create furniture
        tool = FurnitureLayoutTool()
        tool.set_furniture_models(table_path, chair_path)
        
        # Create table and chairs
        furniture = tool.create_table_chairs_from_circle(
            circle_node, 
            num_chairs=num_chairs, 
            chair_inset=chair_inset
        )
        
        # Project to surface if specified
        if surface_node:
            tool.project_furniture_to_surface(
                furniture, 
                surface_node,
                height_offset=height_offset
            )
        
        dialog.accept()
    
    # Connect signals
    circle_button.clicked.connect(on_circle_button_clicked)
    surface_button.clicked.connect(on_surface_button_clicked)
    table_button.clicked.connect(on_table_button_clicked)
    chair_button.clicked.connect(on_chair_button_clicked)
    num_chairs_slider.valueChanged.connect(on_num_chairs_changed)
    chair_inset_slider.valueChanged.connect(on_chair_inset_changed)
    create_button.clicked.connect(on_create_clicked)
    
    # Show dialog
    dialog.exec_()

# Function to add to shelf
def add_to_shelf():
    """Add this tool to a Houdini shelf"""
    # Get all shelves
    shelves = hou.shelves.shelves()
    
    # Find the "digital_assets" shelf or prompt user to select one
    target_shelf = None
    shelf_options = []
    
    for name, shelf in shelves.items():
        shelf_options.append(name)
        if name == "digital_assets":
            target_shelf = shelf
    
    # If digital_assets shelf doesn't exist, ask user to select a shelf
    if target_shelf is None:
        selected = hou.ui.selectFromList(
            shelf_options,
            message="Select a shelf to add the Table & Chairs Tool to:",
            title="Add to Shelf",
            clear_on_cancel=True
        )
        
        if not selected:
            print("Shelf selection cancelled")
            return
            
        target_shelf_name = shelf_options[selected[0]]
        target_shelf = shelves[target_shelf_name]
    
    # Create the tool
    tool_name = "TableChairsTool"
    tool_label = "Table & Chairs"
    tool_script = """import furniture_layout_tool
furniture_layout_tool.create_table_chairs_ui()"""
    
    # Check if tool already exists and remove it
    existing_tools = target_shelf.tools()
    for tool in existing_tools:
        if tool.name() == tool_name:
            target_shelf.removeTool(tool)
    
    # Create and add the new tool
    new_tool = hou.shelves.newTool(
        name=tool_name,
        label=tool_label,
        iconName="SHELF_circle",
        script=tool_script,
        help="Create a table and chairs layout from a circle node"
    )
    
    existing_tools = list(target_shelf.tools())
    existing_tools.append(new_tool)
    target_shelf.setTools(existing_tools)
    
    print(f"Successfully added Table & Chairs Tool to the {target_shelf.name()} shelf")