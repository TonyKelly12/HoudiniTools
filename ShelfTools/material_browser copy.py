"""
Houdini Material Browser with Integrated Importer
-----------------------------------------------
A tool that can both browse existing materials and import new ones
from external texture folders.
"""

import hou
import os
import re
import shutil
from PySide2 import QtCore, QtWidgets, QtGui


class MaterialBrowserWidget(QtWidgets.QMainWindow):
    """Widget for displaying and browsing materials with import functionality"""
    
    def __init__(self, parent=None):
        super(MaterialBrowserWidget, self).__init__(parent)
        self.setWindowTitle("Material Browser & Importer")
        self.resize(1100, 700)
        self.setWindowFlags(QtCore.Qt.Window)
        
        # Create central widget
        self.central_widget = QtWidgets.QWidget()
        self.setCentralWidget(self.central_widget)
        
        # Material data
        self.materials = []
        self.material_icons = {}
        self.texture_folders = {}  # For import functionality
        self.preview_icons = {}    # For import functionality
        
        # Get project path
        self.project_path = hou.text.expandString("$HIP")
        self.tex_path = os.path.join(self.project_path, "tex")
        self.source_tex_path = ""
        self.current_mode = "browser"  # "browser" or "importer"
        
        # Import the Redshift material tool
        self.material_tool = None
        self.import_material_tool()
        
        # Create the UI
        self.create_ui()
    
    def import_material_tool(self):
        """Import the Redshift material tool"""
        try:
            import redshift_material_tool_v2
            self.material_tool = redshift_material_tool_v2.RedshiftMaterialTool()
            print("Successfully imported Redshift material tool")
        except ImportError:
            print("Could not import Redshift material tool")
    
    def create_ui(self):
        """Create the user interface"""
        main_layout = QtWidgets.QVBoxLayout(self.central_widget)
        
        # Create tab widget for browser and importer
        self.tab_widget = QtWidgets.QTabWidget()
        
        # Create browser tab
        browser_widget = QtWidgets.QWidget()
        browser_layout = QtWidgets.QVBoxLayout(browser_widget)
        self.create_browser_ui(browser_layout)
        self.tab_widget.addTab(browser_widget, "Browse Materials")
        
        # Create importer tab
        importer_widget = QtWidgets.QWidget()
        importer_layout = QtWidgets.QVBoxLayout(importer_widget)
        self.create_importer_ui(importer_layout)
        self.tab_widget.addTab(importer_widget, "Import Materials")
        
        # Connect tab changed signal
        self.tab_widget.currentChanged.connect(self.on_tab_changed)
        
        main_layout.addWidget(self.tab_widget)
        
        # Status bar
        self.status_bar = QtWidgets.QStatusBar()
        self.setStatusBar(self.status_bar)
    
    def create_browser_ui(self, layout):
        """Create the browser UI"""
        # Material folder selection
        folder_layout = QtWidgets.QHBoxLayout()
        folder_label = QtWidgets.QLabel("Material Folder:")
        self.folder_path_field = QtWidgets.QLineEdit()
        self.folder_path_field.setText(hou.node("/mat").path() if hou.node("/mat") else "/mat")
        browse_button = QtWidgets.QPushButton("Browse...")
        browse_button.clicked.connect(self.browse_material_folder)
        
        folder_layout.addWidget(folder_label)
        folder_layout.addWidget(self.folder_path_field, 1)
        folder_layout.addWidget(browse_button)
        
        layout.addLayout(folder_layout)
        
        # Texture folder selection
        tex_folder_layout = QtWidgets.QHBoxLayout()
        tex_folder_label = QtWidgets.QLabel("Texture Folder:")
        self.tex_folder_path_field = QtWidgets.QLineEdit()
        self.tex_folder_path_field.setText(self.tex_path)
        tex_browse_button = QtWidgets.QPushButton("Browse...")
        tex_browse_button.clicked.connect(self.browse_texture_folder)
        
        tex_folder_layout.addWidget(tex_folder_label)
        tex_folder_layout.addWidget(self.tex_folder_path_field, 1)
        tex_folder_layout.addWidget(tex_browse_button)
        
        layout.addLayout(tex_folder_layout)
        
        # Browser toolbar
        browser_toolbar = QtWidgets.QHBoxLayout()
        self.refresh_button = QtWidgets.QPushButton("Refresh Materials")
        self.refresh_button.clicked.connect(self.scan_materials)
        
        self.browser_filter_label = QtWidgets.QLabel("Filter:")
        self.browser_filter_input = QtWidgets.QLineEdit()
        self.browser_filter_input.textChanged.connect(lambda text: self.filter_materials(text, "browser"))
        
        browser_toolbar.addWidget(self.refresh_button)
        browser_toolbar.addWidget(self.browser_filter_label)
        browser_toolbar.addWidget(self.browser_filter_input)
        
        layout.addLayout(browser_toolbar)
        
        # Browser scroll area
        browser_scroll_area = QtWidgets.QScrollArea()
        browser_scroll_area.setWidgetResizable(True)
        browser_scroll_widget = QtWidgets.QWidget()
        self.browser_grid_layout = QtWidgets.QGridLayout(browser_scroll_widget)
        self.browser_grid_layout.setAlignment(QtCore.Qt.AlignTop | QtCore.Qt.AlignLeft)
        browser_scroll_area.setWidget(browser_scroll_widget)
        
        layout.addWidget(browser_scroll_area)
    
    def create_importer_ui(self, layout):
        """Create the importer UI"""
        # Source texture folder selection
        source_layout = QtWidgets.QHBoxLayout()
        source_label = QtWidgets.QLabel("Source Texture Folder:")
        self.source_path_field = QtWidgets.QLineEdit()
        browse_button = QtWidgets.QPushButton("Browse...")
        browse_button.clicked.connect(self.browse_source_folder)
        
        source_layout.addWidget(source_label)
        source_layout.addWidget(self.source_path_field, 1)
        source_layout.addWidget(browse_button)
        
        layout.addLayout(source_layout)
        
        # Project texture folder display (read-only)
        project_layout = QtWidgets.QHBoxLayout()
        project_label = QtWidgets.QLabel("Project Texture Folder:")
        self.project_path_field = QtWidgets.QLineEdit()
        self.project_path_field.setText(self.tex_path)
        self.project_path_field.setReadOnly(True)
        self.project_path_field.setStyleSheet("background-color: #2A2A2A;")
        
        project_layout.addWidget(project_label)
        project_layout.addWidget(self.project_path_field, 1)
        
        layout.addLayout(project_layout)
        
        # Importer toolbar
        importer_toolbar = QtWidgets.QHBoxLayout()
        self.scan_button = QtWidgets.QPushButton("Scan for Materials")
        self.scan_button.clicked.connect(self.scan_texture_folders)
        
        self.importer_filter_label = QtWidgets.QLabel("Filter:")
        self.importer_filter_input = QtWidgets.QLineEdit()
        self.importer_filter_input.textChanged.connect(lambda text: self.filter_materials(text, "importer"))
        
        importer_toolbar.addWidget(self.scan_button)
        importer_toolbar.addWidget(self.importer_filter_label)
        importer_toolbar.addWidget(self.importer_filter_input)
        
        layout.addLayout(importer_toolbar)
        
        # Importer scroll area
        importer_scroll_area = QtWidgets.QScrollArea()
        importer_scroll_area.setWidgetResizable(True)
        importer_scroll_widget = QtWidgets.QWidget()
        self.importer_grid_layout = QtWidgets.QGridLayout(importer_scroll_widget)
        self.importer_grid_layout.setAlignment(QtCore.Qt.AlignTop | QtCore.Qt.AlignLeft)
        importer_scroll_area.setWidget(importer_scroll_widget)
        
        layout.addWidget(importer_scroll_area)
    
    def on_tab_changed(self, index):
        """Handle tab change"""
        if index == 0:
            self.current_mode = "browser"
            self.scan_materials()  # Refresh browser view
        else:
            self.current_mode = "importer"
    
    def browse_material_folder(self):
        """Open a Houdini node browser to select the material folder"""
        current_path = self.folder_path_field.text()
        
        node_path = hou.ui.selectNode(
            title="Select Material Folder",
            initial_node=hou.node(current_path) if hou.node(current_path) else None,
            node_type_filter=hou.nodeTypeFilter.NoFilter,
            width=400,
            height=400
        )
        
        if node_path:
            self.folder_path_field.setText(node_path)
            self.scan_materials()
    
    def browse_texture_folder(self):
        """Open a file browser to select the texture folder"""
        directory = QtWidgets.QFileDialog.getExistingDirectory(
            self,
            "Select Texture Folder",
            self.tex_path
        )
        
        if directory:
            self.tex_path = directory
            self.tex_folder_path_field.setText(directory)
            self.scan_materials()
    
    def browse_source_folder(self):
        """Open a file browser to select the source texture folder"""
        directory = QtWidgets.QFileDialog.getExistingDirectory(
            self,
            "Select Source Texture Folder",
            self.source_path_field.text() or hou.text.expandString("$HOME")
        )
        
        if directory:
            self.source_tex_path = directory
            self.source_path_field.setText(directory)
            self.scan_texture_folders()
    
    def scan_materials(self):
        """Scan the Houdini project for materials and find their icons"""
        self.status_bar.showMessage("Scanning for materials...")
        self.materials = []
        self.material_icons = {}
        
        # Clear the browser grid layout
        self.clear_grid_layout(self.browser_grid_layout)
        
        mat_path = self.folder_path_field.text()
        mat_context = hou.node(mat_path)
        
        if not mat_context:
            self.status_bar.showMessage(f"Material folder not found: {mat_path}")
            return
        
        self.tex_path = self.tex_folder_path_field.text()
        
        # Check all top-level nodes in material context
        for node in mat_context.children():
            if node.type().name() == "redshift_vopnet":
                self.materials.append(node)
                icon_path = self.find_icon_for_material(node)
                if icon_path:
                    self.material_icons[node.path()] = icon_path
            
            elif node.type().name() == "subnet":
                self.scan_subnet_for_materials(node)
        
        # Update the browser grid
        self.populate_browser_grid()
        self.status_bar.showMessage(f"Found {len(self.materials)} materials, {len(self.material_icons)} with icons.")
    
    def scan_texture_folders(self):
        """Scan the source folder for texture sets with icons"""
        if not self.source_tex_path or not os.path.exists(self.source_tex_path):
            self.status_bar.showMessage("Please select a valid source texture folder")
            return

        self.status_bar.showMessage("Scanning for texture folders...")
        self.texture_folders = {}
        self.preview_icons = {}
        self.folder_hierarchy = {}

        # Clear the importer grid layout
        self.clear_grid_layout(self.importer_grid_layout)

        # First pass: Scan for texture folders and build hierarchy
        for root, dirs, files in os.walk(self.source_tex_path):
            # Skip empty directories
            if not files:
                continue

            # Check for textures and icons
            texture_files = []
            icon_file = None

            for file in files:
                if file.lower() in ["icon.jpg", "icon.jpeg", "icon.png"]:
                    icon_file = os.path.join(root, file)

                if any(
                    file.lower().endswith(ext)
                    for ext in [".jpg", ".jpeg", ".png", ".tif", ".tiff", ".exr", ".tx"]
                ):
                    texture_files.append(file)

            # Get relative path from source to current folder
            rel_path = os.path.relpath(root, self.source_tex_path)
            path_parts = rel_path.split(os.sep) if rel_path != "." else []
            
            # Determine folder type
            folder_type = "root"
            parent_path = None
            
            if path_parts:
                if len(path_parts) == 1:
                    folder_type = "collection"
                elif len(path_parts) == 2:
                    folder_type = "variant"
                    parent_path = os.path.dirname(root)
                elif len(path_parts) == 3:
                    folder_type = "mesh"
                    parent_path = os.path.dirname(root)
                else:
                    # Deeper nesting - continue pattern
                    folder_type = "mesh" if texture_files else "collection"
                    parent_path = os.path.dirname(root)

            # If it has textures or is a collection/variant, add it
            if texture_files or folder_type in ["collection", "variant"]:
                folder_name = os.path.basename(root)
                self.texture_folders[root] = {
                    "name": folder_name,
                    "textures": texture_files,
                    "icon": icon_file,
                    "type": folder_type,
                    "parent": parent_path,
                    "children": [],
                    "rel_path": rel_path
                }

                if icon_file:
                    self.preview_icons[root] = icon_file

        # Second pass: Build hierarchy relationships
        for folder_path in list(self.texture_folders.keys()):
            folder_info = self.texture_folders[folder_path]
            parent_path = folder_info["parent"]
            
            if parent_path and parent_path in self.texture_folders:
                self.texture_folders[parent_path]["children"].append(folder_path)
                
        # Find root level folders
        self.root_folders = []
        for folder_path, folder_info in self.texture_folders.items():
            if folder_info["type"] == "collection" and not folder_info["parent"]:
                self.root_folders.append(folder_path)
            elif folder_info["type"] == "root":
                self.root_folders.append(folder_path)

        # Update the importer grid to show hierarchical structure
        self.populate_importer_grid()
        self.status_bar.showMessage(
            f"Found {len(self.texture_folders)} texture folders"
        )
    
    def populate_browser_grid(self):
        """Populate the browser grid with material preview cards"""
        columns = 4
        
        for index, material in enumerate(self.materials):
            row = index // columns
            col = index % columns
            
            cell = self.create_material_cell(material, "browser")
            self.browser_grid_layout.addWidget(cell, row, col)
    
    def populate_importer_grid(self):
        """Populate the importer grid with texture folder preview cards"""
        columns = 4
        
        for index, (folder_path, folder_info) in enumerate(self.texture_folders.items()):
            row = index // columns
            col = index % columns
            
            cell = self.create_material_cell((folder_path, folder_info), "importer")
            self.importer_grid_layout.addWidget(cell, row, col)
    
    def create_material_cell(self, data, mode):
        """Create a widget cell for either a material or texture folder"""
        cell_widget = QtWidgets.QWidget()
        cell_layout = QtWidgets.QVBoxLayout()
        cell_widget.setLayout(cell_layout)
        cell_widget.setFixedSize(220, 240)
        
        # Create preview image
        preview_label = QtWidgets.QLabel()
        preview_label.setFixedSize(200, 200)
        preview_label.setAlignment(QtCore.Qt.AlignCenter)
        preview_label.setStyleSheet("background-color: #333333; border: 1px solid #555555;")
        
        if mode == "browser":
            # Handle material preview
            material = data
            if material.path() in self.material_icons:
                icon_path = self.material_icons[material.path()]
                if os.path.exists(icon_path):
                    pixmap = QtGui.QPixmap(icon_path)
                    if not pixmap.isNull():
                        preview_label.setPixmap(pixmap.scaled(
                            200, 200, 
                            QtCore.Qt.KeepAspectRatio, 
                            QtCore.Qt.SmoothTransformation
                        ))
                    else:
                        preview_label.setText("Icon Error")
                else:
                    preview_label.setText("Icon Missing")
            else:
                preview_label.setText("No Preview\nAvailable")
                preview_label.setStyleSheet("color: #888888; background-color: #333333; border: 1px solid #555555; font-size: 14px;")
            
            display_name = material.name()
            if display_name.startswith("RS_"):
                display_name = display_name[3:]
            
            name_label = QtWidgets.QLabel(display_name)
            name_label.setAlignment(QtCore.Qt.AlignCenter)
            name_label.setStyleSheet("color: white; font-weight: bold;")
            
            cell_layout.addWidget(preview_label)
            cell_layout.addWidget(name_label)
            
            # Connect events
            cell_widget.mouseDoubleClickEvent = lambda event, m=material: self.on_material_double_clicked(m)
            cell_widget.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
            cell_widget.customContextMenuRequested.connect(
                lambda pos, m=material: self.show_context_menu(pos, m)
            )
        
        else:
            # Handle texture folder preview
            folder_path, folder_info = data
            if folder_info["icon"] and os.path.exists(folder_info["icon"]):
                pixmap = QtGui.QPixmap(folder_info["icon"])
                if not pixmap.isNull():
                    preview_label.setPixmap(pixmap.scaled(
                        200, 200, 
                        QtCore.Qt.KeepAspectRatio, 
                        QtCore.Qt.SmoothTransformation
                    ))
                else:
                    preview_label.setText("Icon Error")
            else:
                preview_label.setText("No Preview\nAvailable")
                preview_label.setStyleSheet("color: #888888; background-color: #333333; border: 1px solid #555555; font-size: 14px;")
            
            name_label = QtWidgets.QLabel(folder_info["name"])
            name_label.setAlignment(QtCore.Qt.AlignCenter)
            name_label.setStyleSheet("color: white; font-weight: bold;")
            
            count_label = QtWidgets.QLabel(f"{len(folder_info['textures'])} textures")
            count_label.setAlignment(QtCore.Qt.AlignCenter)
            count_label.setStyleSheet("color: #888888; font-size: 10px;")
            
            cell_layout.addWidget(preview_label)
            cell_layout.addWidget(name_label)
            cell_layout.addWidget(count_label)
            
            # Connect click event for import
            cell_widget.mousePressEvent = lambda event, path=folder_path: self.on_texture_folder_clicked(path)
        
        # Add hover effect
        cell_widget.setStyleSheet("""
            QWidget {
                border: 1px solid #333333;
                border-radius: 4px;
            }
            QWidget:hover {
                border: 1px solid #666666;
                background-color: #2A2A2A;
            }
        """)
        
        return cell_widget
    
    def on_texture_folder_clicked(self, folder_path):
        """Handle click on a texture folder cell - import the material"""
        folder_info = self.texture_folders[folder_path]
        folder_name = folder_info["name"]
        
        reply = QtWidgets.QMessageBox.question(
            self,
            "Import Material",
            f"Import material '{folder_name}'?\n\nThis will:\n1. Copy textures to project folder\n2. Create a Redshift material",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            QtWidgets.QMessageBox.Yes
        )
        
        if reply == QtWidgets.QMessageBox.Yes:
            self.import_material(folder_path, folder_info)
    
    def import_material(self, source_folder, folder_info):
        """Import the material: copy textures and create Redshift material"""
        folder_name = folder_info["name"]
        
        try:
            if not os.path.exists(self.tex_path):
                os.makedirs(self.tex_path)
            
            dest_folder = os.path.join(self.tex_path, folder_name)
            if os.path.exists(dest_folder):
                reply = QtWidgets.QMessageBox.question(
                    self,
                    "Folder Exists",
                    f"Folder '{folder_name}' already exists in project. Overwrite?",
                    QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                    QtWidgets.QMessageBox.No
                )
                
                if reply == QtWidgets.QMessageBox.No:
                    return
                
                shutil.rmtree(dest_folder)
            
            # Copy the entire folder
            self.status_bar.showMessage(f"Copying textures for {folder_name}...")
            shutil.copytree(source_folder, dest_folder)
            
            # Create the Redshift material
            if self.material_tool:
                self.status_bar.showMessage(f"Creating material for {folder_name}...")
                
                self.material_tool.tex_path = self.tex_path
                material_sets = self.material_tool.scan_textures()
                mat_context = self.material_tool.create_material_context()
                
                material_created = False
                for mesh_name, materials in material_sets.items():
                    if mesh_name == folder_name:
                        for material_name, textures in materials.items():
                            new_mat = self.material_tool.create_redshift_material(
                                mat_context, material_name, textures
                            )
                            if new_mat:
                                material_created = True
                                self.status_bar.showMessage(f"Successfully imported {material_name}")
                
                if not material_created:
                    self.status_bar.showMessage(f"Warning: Textures copied but no material created for {folder_name}")
                
                # Switch to browser tab and refresh
                self.tab_widget.setCurrentIndex(0)
                self.scan_materials()
            else:
                self.status_bar.showMessage(f"Textures copied to project. Material tool not available.")
        
        except Exception as e:
            QtWidgets.QMessageBox.critical(
                self,
                "Import Error",
                f"Error importing material: {str(e)}"
            )
            self.status_bar.showMessage(f"Error importing {folder_name}")
    
    def scan_subnet_for_materials(self, subnet):
        """Recursively scan a subnet for materials"""
        for child in subnet.children():
            if child.type().name() == "redshift_vopnet":
                self.materials.append(child)
                icon_path = self.find_icon_for_material(child)
                if icon_path:
                    self.material_icons[child.path()] = icon_path
            elif child.type().name() == "subnet":
                self.scan_subnet_for_materials(child)
    
    def find_icon_for_material(self, material):
        """Find an icon file for the given material"""
        material_name = material.name()
        if material_name.startswith("RS_"):
            material_name = material_name[3:]
        
        parent = material.parent()
        is_in_folder = parent.type().name() == "subnet" and parent.name().startswith("FOLDER_")
        
        if is_in_folder:
            folder_name = parent.name().replace("FOLDER_", "")
            texture_folder = os.path.join(self.tex_path, folder_name)
        else:
            texture_folder = os.path.join(self.tex_path, material_name)
        
        if os.path.exists(texture_folder):
            for ext in [".jpg", ".jpeg", ".png"]:
                icon_path = os.path.join(texture_folder, f"icon{ext}")
                if os.path.exists(icon_path):
                    return icon_path
                
                icon_path = os.path.join(texture_folder, f"icon{ext.upper()}")
                if os.path.exists(icon_path):
                    return icon_path
        
        if os.path.exists(self.tex_path):
            for root, dirs, files in os.walk(self.tex_path):
                for file in files:
                    if file.lower() in ["icon.jpg", "icon.jpeg", "icon.png"]:
                        texture_files = [f for f in files if any(f.lower().endswith(ext) 
                                        for ext in [".jpg", ".jpeg", ".png", ".tif", ".tiff", ".exr", ".tx"])]
                        
                        for tex_file in texture_files:
                            if material_name.lower() in tex_file.lower():
                                return os.path.join(root, file)
        
        return None
    
    def clear_grid_layout(self, layout):
        """Clear all items from a grid layout"""
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
    
    def filter_materials(self, filter_text, mode):
        """Filter materials based on the filter text"""
        if mode == "browser":
            self.clear_grid_layout(self.browser_grid_layout)
            
            if not filter_text:
                self.populate_browser_grid()
                return
            
            filtered_materials = [m for m in self.materials if filter_text.lower() in m.name().lower()]
            columns = 4
            
            for index, material in enumerate(filtered_materials):
                row = index // columns
                col = index % columns
                cell = self.create_material_cell(material, "browser")
                self.browser_grid_layout.addWidget(cell, row, col)
            
            self.status_bar.showMessage(f"Showing {len(filtered_materials)} of {len(self.materials)} materials")
        
        else:  # importer mode
            self.clear_grid_layout(self.importer_grid_layout)
            
            if not filter_text:
                self.populate_importer_grid()
                return
            
            filtered_folders = {path: info for path, info in self.texture_folders.items() 
                              if filter_text.lower() in info["name"].lower()}
            columns = 4
            
            for index, (folder_path, folder_info) in enumerate(filtered_folders.items()):
                row = index // columns
                col = index % columns
                cell = self.create_material_cell((folder_path, folder_info), "importer")
                self.importer_grid_layout.addWidget(cell, row, col)
            
            self.status_bar.showMessage(f"Showing {len(filtered_folders)} of {len(self.texture_folders)} materials")
    
    def show_context_menu(self, pos, material):
        """Show context menu for material cell"""
        context_menu = QtWidgets.QMenu(self)
        
        open_action = context_menu.addAction("Open in Network Editor")
        open_action.triggered.connect(lambda: self.on_material_double_clicked(material))
        
        assign_action = context_menu.addAction("Assign to Selected Objects")
        assign_action.triggered.connect(lambda: self.assign_material_to_selection(material))
        
        context_menu.exec_(QtGui.QCursor.pos())
    
    def assign_material_to_selection(self, material):
        """Assign the material to currently selected objects"""
        try:
            selection = hou.selectedNodes()
            geo_nodes = [node for node in selection 
                        if node.type().category().name() == "Object" 
                        and node.type().name() in ["geo", "subnet"]]
            
            if not geo_nodes:
                self.status_bar.showMessage("No valid geometry objects selected")
                return
            
            for node in geo_nodes:
                if "shop_materialpath" in [p.name() for p in node.parms()]:
                    node.parm("shop_materialpath").set(material.path())
            
            self.status_bar.showMessage(f"Assigned {material.name()} to {len(geo_nodes)} objects")
        
        except Exception as e:
            self.status_bar.showMessage(f"Error assigning material: {str(e)}")
    
    def on_material_double_clicked(self, material):
        """Handle double-click on a material cell"""
        material.setSelected(True)
        hou.ui.paneTabOfType(hou.paneTabType.NetworkEditor).setCurrentNode(material)
        self.status_bar.showMessage(f"Selected material: {material.name()}")


def launch_material_browser():
    """Launch the material browser tool"""
    browser = MaterialBrowserWidget(hou.ui.mainQtWindow())
    browser.show()
    browser.scan_materials()
    return browser


# Store browser instance to prevent garbage collection
_browser_instance = None


def show_material_browser():
    """Show the material browser tool (creates a new instance if needed)"""
    global _browser_instance
    
    if _browser_instance and not _browser_instance.isVisible():
        _browser_instance.show()
        _browser_instance.raise_()
        _browser_instance.activateWindow()
    else:
        _browser_instance = launch_material_browser()
    
    return _browser_instance


# Entry point for standalone use
if __name__ == "__main__":
    show_material_browser()
    