"""
Houdini Material Browser Tool
-----------------------------
A tool that scans Redshift materials in a Houdini project and displays
them in a grid layout with preview renders.
"""

import hou
import os
import re
import tempfile
import time
from PySide2 import QtCore, QtWidgets, QtGui


class MaterialPreviewGenerator:
    """Class to handle creating preview renders of materials"""

    def __init__(self):
        self.preview_size = 256
        self.temp_dir = tempfile.gettempdir()

        # Check if Redshift is available
        self.redshift_available = self._check_redshift_available()

    def _check_redshift_available(self):
        """Check if Redshift is available in this Houdini installation"""
        try:
            # Check for Redshift node types
            redshift_nodes = [
                nt
                for nt in hou.nodeTypeCategories()["Vop"].nodeTypes().values()
                if "redshift" in nt.name().lower()
            ]

            # Also check in ROP category
            rop_redshift = hou.nodeType(hou.ropNodeTypeCategory(), "Redshift_ROP")

            # If we found Redshift nodes or ROP, it's available
            return len(redshift_nodes) > 0 or rop_redshift is not None
        except:
            return False

    def setup_preview_scene(self):
        """Create a temporary scene for rendering material previews"""
        # Store current scene state
        current_desktop = hou.ui.curDesktop()
        current_scene_viewer = current_desktop.paneTabOfType(
            hou.paneTabType.SceneViewer
        )

        # Clean up any existing preview nodes first (in case of previous errors)
        self.cleanup_existing_preview_nodes()

        # Create preview objects
        preview_obj = hou.node("/obj").createNode("geo", "preview_sphere")

        # Instead of trying to delete the default file1 node (which may not exist),
        # just create our sphere directly
        sphere = preview_obj.createNode("sphere", "preview_sphere_geo")
        sphere.parm("type").set(0)  # Set to polygon sphere
        sphere.parm("radx").set(1.0)
        sphere.parm("rady").set(1.0)
        sphere.parm("radz").set(1.0)
        sphere.parm("rows").set(32)
        sphere.parm("cols").set(32)

        # Make sure the sphere is connected to the output
        output_node = None
        for node in preview_obj.children():
            if node.type().name() == "null" and node.name() == "OUT":
                output_node = node
                break

        if not output_node:
            output_node = preview_obj.createNode("null", "OUT")

        output_node.setInput(0, sphere)

        # Create a camera for consistent viewing
        cam = hou.node("/obj").createNode("cam", "preview_cam")
        cam.parmTuple("t").set((0, 0, 4))  # Position camera
        cam.parm("focal").set(50)  # 50mm lens

        # Create lights
        key_light = hou.node("/obj").createNode("hlight", "key_light")
        key_light.parmTuple("t").set((3, 3, 5))
        key_light.parm("light_intensity").set(1.5)

        fill_light = hou.node("/obj").createNode("hlight", "fill_light")
        fill_light.parmTuple("t").set((-4, 1, 3))
        fill_light.parm("light_intensity").set(0.7)

        rim_light = hou.node("/obj").createNode("hlight", "rim_light")
        rim_light.parmTuple("t").set((0, -3, -5))
        rim_light.parm("light_intensity").set(1.0)

        # Return the sphere for material assignment
        return preview_obj, cam

    def cleanup_existing_preview_nodes(self):
        """Clean up any existing preview nodes to avoid conflicts"""
        for node_path in [
            "/obj/preview_sphere",
            "/obj/preview_cam",
            "/obj/key_light",
            "/obj/fill_light",
            "/obj/rim_light",
        ]:
            node = hou.node(node_path)
            if node:
                try:
                    node.destroy()
                except:
                    pass

        # Also clean up any preview ROPs in /out
        out_node = hou.node("/out")
        if out_node:
            for child in out_node.children():
                if child.name().startswith("preview_"):
                    try:
                        child.destroy()
                    except:
                        pass

    def generate_preview(self, material_node, preview_obj, camera):
        """Generate a preview image for a given material"""
        try:
            material_path = material_node.path()
            material_name = material_node.name()

            # Create a safe name for the output file (remove invalid characters)
            safe_name = re.sub(r'[\\/*?:"<>|]', "_", material_name)

            # Assign material to preview object
            if not preview_obj.parm("shop_materialpath"):
                print(f"Error: Preview object missing 'shop_materialpath' parameter")
                return None

            preview_obj.parm("shop_materialpath").set(material_path)

            # Set up Redshift render settings
            out_node = hou.node("/out")
            if not out_node:
                print("Error: Unable to find /out context")
                return None

            # Check if Redshift_ROP node type exists
            redshift_rop_type = hou.nodeType(hou.ropNodeTypeCategory(), "Redshift_ROP")
            if not redshift_rop_type:
                print("Error: Redshift_ROP node type not found. Is Redshift installed?")
                return None

            # Create the ROP node
            rop_name = f"preview_{safe_name}"
            rop = out_node.createNode("Redshift_ROP", rop_name)

            # Print all available parameters to debug (temporarily)
            print(
                f"Available parameters in Redshift_ROP: {[p.name() for p in rop.parms()]}"
            )

            # Set camera parameter with multiple attempts
            camera_param_names = ["RS_renderCamera", "camera", "RS_camera"]
            camera_set = False
            for param_name in camera_param_names:
                if rop.parm(param_name):
                    rop.parm(param_name).set(camera.path())
                    camera_set = True
                    break

            if not camera_set:
                print("Error: Could not find camera parameter in Redshift ROP")
                rop.destroy()
                return None

            # Try different resolution parameter names
            # First, check if we need to enable resolution override
            override_params = [
                "RS_overrideCameraRes",
                "override_camera_res",
                "override_camerares",
            ]
            for param_name in override_params:
                if rop.parm(param_name):
                    rop.parm(param_name).set(1)
                    break

            # Set resolution X
            resX_params = [
                "RS_overrideResX",
                "override_res_x",
                "res_overridex",
                "res_x",
            ]
            resX_set = False
            for param_name in resX_params:
                if rop.parm(param_name):
                    rop.parm(param_name).set(self.preview_size)
                    resX_set = True
                    break

            # Set resolution Y
            resY_params = [
                "RS_overrideResY",
                "override_res_y",
                "res_overridey",
                "res_y",
            ]
            resY_set = False
            for param_name in resY_params:
                if rop.parm(param_name):
                    rop.parm(param_name).set(self.preview_size)
                    resY_set = True
                    break

            # If we couldn't set resolution overrides, try the main resolution parameters
            if not resX_set or not resY_set:
                resX_main_params = ["res_x", "resolutionx", "resx"]
                resY_main_params = ["res_y", "resolutiony", "resy"]

                for param_name in resX_main_params:
                    if rop.parm(param_name):
                        rop.parm(param_name).set(self.preview_size)
                        resX_set = True
                        break

                for param_name in resY_main_params:
                    if rop.parm(param_name):
                        rop.parm(param_name).set(self.preview_size)
                        resY_set = True
                        break

            # Set output path for the render
            output_params = [
                "RS_outputFileNamePrefix",
                "RS_outputFilePrefix",
                "output_filename",
                "RS_output_file",
                "picture",
            ]
            output_path = os.path.join(
                tempfile.gettempdir(), f"{safe_name}_preview.jpg"
            )
            output_set = False

            for param_name in output_params:
                if rop.parm(param_name):
                    rop.parm(param_name).set(output_path)
                    output_set = True
                    break

            if not output_set:
                print("Error: Could not find output parameter in Redshift ROP")
                rop.destroy()
                return None

            # Additional settings to ensure render completes successfully
            # Set some common Redshift settings with try/except for each one
            try:
                if rop.parm("RS_unifiedMaxSamples"):
                    rop.parm("RS_unifiedMaxSamples").set(
                        16
                    )  # Lower samples for preview
                elif rop.parm("UnifiedMaxSamples"):
                    rop.parm("UnifiedMaxSamples").set(16)
            except:
                pass

            try:
                if rop.parm("RS_unifiedMinSamples"):
                    rop.parm("RS_unifiedMinSamples").set(4)  # Lower samples for preview
                elif rop.parm("UnifiedMinSamples"):
                    rop.parm("UnifiedMinSamples").set(4)
            except:
                pass

            # Check if execute/render param exists
            render_params = ["execute", "render", "execute_render"]
            render_param = None

            for param_name in render_params:
                if rop.parm(param_name):
                    render_param = rop.parm(param_name)
                    break

            if not render_param:
                print("Error: 'execute' parameter not found in Redshift ROP")
                rop.destroy()
                return None

            # Render
            render_param.pressButton()

            # Wait for render to complete (with timeout)
            timeout = 30  # seconds
            start_time = time.time()
            while not os.path.exists(output_path):
                time.sleep(0.1)
                if time.time() - start_time > timeout:
                    print(f"Error: Render timeout for {material_name}")
                    break

            # Clean up ROP node
            rop.destroy()

            # Check if the file was created
            if os.path.exists(output_path):
                return output_path
            else:
                print(f"Error: Render failed to create output file for {material_name}")
                return None

        except Exception as e:
            import traceback

            traceback.print_exc()
            print(f"Error generating preview for {material_node.name()}: {str(e)}")
            return None

    def cleanup_preview_scene(self, preview_obj, camera):
        """Clean up temporary preview scene nodes"""
        for node in hou.node("/obj").children():
            if node.name().startswith(
                ("preview_", "key_light", "fill_light", "rim_light")
            ):
                node.destroy()


class MaterialBrowserWidget(QtWidgets.QMainWindow):
    """Widget for displaying and browsing materials"""

    def __init__(self, parent=None):
        super(MaterialBrowserWidget, self).__init__(parent)
        self.setWindowTitle("Houdini Material Browser")
        self.resize(900, 600)
        self.setWindowFlags(QtCore.Qt.Window)  # Make it a separate window

        # Create central widget
        self.central_widget = QtWidgets.QWidget()
        self.setCentralWidget(self.central_widget)

        # Create the UI
        self.create_ui()

        # Material data
        self.materials = []
        self.material_previews = {}
        self.preview_generator = MaterialPreviewGenerator()

    def create_ui(self):
        """Create the user interface"""
        main_layout = QtWidgets.QVBoxLayout(self.central_widget)

        # Menu bar
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu("File")

        # Add actions to file menu
        refresh_action = QtWidgets.QAction("Refresh Materials", self)
        refresh_action.triggered.connect(self.scan_materials)
        file_menu.addAction(refresh_action)

        generate_action = QtWidgets.QAction("Generate All Previews", self)
        generate_action.triggered.connect(self.generate_all_previews)
        file_menu.addAction(generate_action)

        test_action = QtWidgets.QAction("Test Preview Single Material", self)
        test_action.triggered.connect(self.test_single_preview)
        file_menu.addAction(test_action)

        file_menu.addSeparator()

        exit_action = QtWidgets.QAction("Close", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Toolbar
        toolbar = QtWidgets.QHBoxLayout()
        self.refresh_button = QtWidgets.QPushButton("Refresh Materials")
        self.refresh_button.clicked.connect(self.scan_materials)

        self.filter_label = QtWidgets.QLabel("Filter:")
        self.filter_input = QtWidgets.QLineEdit()
        self.filter_input.textChanged.connect(self.filter_materials)

        self.generate_previews_button = QtWidgets.QPushButton("Generate Previews")
        self.generate_previews_button.clicked.connect(self.generate_all_previews)

        toolbar.addWidget(self.refresh_button)
        toolbar.addWidget(self.filter_label)
        toolbar.addWidget(self.filter_input)
        toolbar.addWidget(self.generate_previews_button)

        main_layout.addLayout(toolbar)

        # Scroll area for material grid
        scroll_area = QtWidgets.QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_widget = QtWidgets.QWidget()
        self.grid_layout = QtWidgets.QGridLayout(scroll_widget)
        self.grid_layout.setAlignment(QtCore.Qt.AlignTop | QtCore.Qt.AlignLeft)
        scroll_area.setWidget(scroll_widget)

        main_layout.addWidget(scroll_area)

        # Status bar
        self.status_bar = QtWidgets.QStatusBar()
        self.setStatusBar(self.status_bar)

    def scan_materials(self):
        """Scan the Houdini project for materials"""
        self.status_bar.showMessage("Scanning for materials...")
        self.materials = []

        # Clear the grid layout
        self.clear_grid_layout()

        # Look for materials in /mat context
        mat_context = hou.node("/mat")
        if not mat_context:
            self.status_bar.showMessage("No /mat context found.")
            return

        # Check all top-level nodes in /mat
        for node in mat_context.children():
            # For standard Redshift materials
            if node.type().name() == "redshift_vopnet":
                self.materials.append(node)

            # For materials in folders
            elif node.type().name() == "subnet":
                # Check if this is a material folder
                if node.name().startswith("FOLDER_"):
                    for child in node.children():
                        if child.type().name() == "redshift_vopnet":
                            self.materials.append(child)

        # Update the UI
        self.populate_grid()
        self.status_bar.showMessage(f"Found {len(self.materials)} materials.")

    def clear_grid_layout(self):
        """Clear all items from the grid layout"""
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

    def populate_grid(self):
        """Populate the grid with material previews/placeholders"""
        columns = 4  # Number of columns in the grid

        for index, material in enumerate(self.materials):
            row = index // columns
            col = index % columns

            # Create material cell widget
            cell = self.create_material_cell(material)
            self.grid_layout.addWidget(cell, row, col)

    def create_material_cell(self, material):
        """Create a widget cell for a material"""
        cell_widget = QtWidgets.QWidget()
        cell_layout = QtWidgets.QVBoxLayout()
        cell_widget.setLayout(cell_layout)

        # Create preview image or placeholder
        preview_label = QtWidgets.QLabel()
        preview_label.setFixedSize(200, 200)
        preview_label.setAlignment(QtCore.Qt.AlignCenter)
        preview_label.setStyleSheet(
            "background-color: #333333; border: 1px solid #555555;"
        )

        try:
            # Set placeholder text
            if material.path() in self.material_previews and os.path.exists(
                self.material_previews[material.path()]
            ):
                # Use cached preview if available
                pixmap = QtGui.QPixmap(self.material_previews[material.path()])
                if not pixmap.isNull():
                    preview_label.setPixmap(
                        pixmap.scaled(
                            200,
                            200,
                            QtCore.Qt.KeepAspectRatio,
                            QtCore.Qt.SmoothTransformation,
                        )
                    )
                else:
                    # If pixmap couldn't be loaded
                    preview_label.setText("Preview Error")
                    preview_label.setStyleSheet(
                        "color: white; background-color: #333333; border: 1px solid #555555;"
                    )
            else:
                # Create placeholder with material sphere icon
                sphere_icon = QtWidgets.QApplication.style().standardIcon(
                    QtWidgets.QStyle.SP_TitleBarMenuButton
                )
                if not sphere_icon.isNull():
                    preview_label.setPixmap(sphere_icon.pixmap(64, 64))
                else:
                    # Text fallback
                    preview_label.setText("No Preview")
                    preview_label.setStyleSheet(
                        "color: white; background-color: #333333; border: 1px solid #555555;"
                    )

            # Clean material name (remove RS_ prefix if present)
            display_name = material.name()
            if display_name.startswith("RS_"):
                display_name = display_name[3:]

            # Create name label
            name_label = QtWidgets.QLabel(display_name)
            name_label.setAlignment(QtCore.Qt.AlignCenter)
            name_label.setStyleSheet("color: white; font-weight: bold;")

            # Create "NEW" label
            # In a real implementation, we could check creation time compared to a threshold
            # For now, we'll add it to match the example image
            new_label = QtWidgets.QLabel("NEW")
            new_label.setAlignment(QtCore.Qt.AlignCenter)
            new_label.setStyleSheet(
                "color: white; background-color: #555555; font-weight: bold; padding: 2px;"
            )

            # Add widgets to layout
            cell_layout.addWidget(new_label)
            cell_layout.addWidget(preview_label)
            cell_layout.addWidget(name_label)

            # Connect double-click event
            cell_widget.mouseDoubleClickEvent = (
                lambda event, m=material: self.on_material_double_clicked(m)
            )

            # Add right-click context menu
            cell_widget.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
            cell_widget.customContextMenuRequested.connect(
                lambda pos, m=material: self.show_context_menu(pos, m)
            )

        except Exception as e:
            # If anything fails, create a minimal cell
            error_label = QtWidgets.QLabel(f"Error: {str(e)}")
            error_label.setStyleSheet("color: red;")
            cell_layout.addWidget(error_label)

        return cell_widget

    def show_context_menu(self, pos, material):
        """Show context menu for material cell"""
        context_menu = QtWidgets.QMenu(self)

        # Add menu actions
        open_action = context_menu.addAction("Open in Network Editor")
        open_action.triggered.connect(lambda: self.on_material_double_clicked(material))

        assign_action = context_menu.addAction("Assign to Selected Objects")
        assign_action.triggered.connect(
            lambda: self.assign_material_to_selection(material)
        )

        refresh_action = context_menu.addAction("Refresh Preview")
        refresh_action.triggered.connect(lambda: self.refresh_single_preview(material))

        # Show the menu
        context_menu.exec_(QtGui.QCursor.pos())

    def assign_material_to_selection(self, material):
        """Assign the material to currently selected objects"""
        try:
            # Get selected nodes in the viewport
            selection = hou.selectedNodes()

            # Filter only geometry nodes
            geo_nodes = [
                node
                for node in selection
                if node.type().category().name() == "Object"
                and node.type().name() in ["geo", "subnet"]
            ]

            if not geo_nodes:
                self.status_bar.showMessage("No valid geometry objects selected")
                return

            # Assign material to each selected node
            for node in geo_nodes:
                if "shop_materialpath" in [p.name() for p in node.parms()]:
                    node.parm("shop_materialpath").set(material.path())

            self.status_bar.showMessage(
                f"Assigned {material.name()} to {len(geo_nodes)} objects"
            )

        except Exception as e:
            self.status_bar.showMessage(f"Error assigning material: {str(e)}")

    def refresh_single_preview(self, material):
        """Refresh the preview for a single material"""
        try:
            # Show busy cursor
            QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)

            # Check if Redshift is available
            if not self.preview_generator.redshift_available:
                self.status_bar.showMessage(
                    "Error: Redshift is not available. Cannot generate preview."
                )
                QtWidgets.QApplication.restoreOverrideCursor()
                return

            # Setup preview scene
            preview_obj, camera = self.preview_generator.setup_preview_scene()

            if not preview_obj or not camera:
                self.status_bar.showMessage(
                    "Failed to create preview scene. Check the console for errors."
                )
                QtWidgets.QApplication.restoreOverrideCursor()
                return

            try:
                # Check if material exists (don't use isValid)
                if not material.path() or not hou.node(material.path()):
                    self.status_bar.showMessage(
                        f"Error: Material {material.name()} is not valid"
                    )
                    QtWidgets.QApplication.restoreOverrideCursor()
                    return

                # Generate preview
                preview_path = self.preview_generator.generate_preview(
                    material, preview_obj, camera
                )
                if preview_path:
                    self.material_previews[material.path()] = preview_path
                    self.status_bar.showMessage(
                        f"Updated preview for {material.name()}"
                    )
                else:
                    self.status_bar.showMessage(
                        f"Failed to generate preview for {material.name()}"
                    )
            finally:
                # Clean up preview scene
                self.preview_generator.cleanup_preview_scene(preview_obj, camera)

            # Rebuild the grid to show the updated preview
            self.populate_grid()

        except Exception as e:
            self.status_bar.showMessage(f"Error refreshing preview: {str(e)}")
        finally:
            # Restore cursor
            QtWidgets.QApplication.restoreOverrideCursor()

    def on_material_double_clicked(self, material):
        """Handle double-click on a material cell"""
        # You could implement different actions here, like:
        # 1. Open the material network
        # 2. Assign the material to selected objects
        # 3. Show material properties

        # For now, we'll just open the material network
        material.setSelected(True)
        hou.ui.paneTabOfType(hou.paneTabType.NetworkEditor).setCurrentNode(material)

        self.status_bar.showMessage(f"Selected material: {material.name()}")

    def generate_all_previews(self):
        """Generate preview renders for all materials"""
        if not self.materials:
            self.status_bar.showMessage(
                "No materials to preview. Please scan for materials first."
            )
            return

        # Check if Redshift is available
        if not self.preview_generator.redshift_available:
            self.status_bar.showMessage(
                "Error: Redshift is not available. Cannot generate previews."
            )
            # Show error dialog
            QtWidgets.QMessageBox.critical(
                self,
                "Redshift Not Available",
                "Redshift does not appear to be installed or is not properly configured in Houdini.\n\n"
                "The material browser can still be used to browse materials, but preview generation requires Redshift.",
            )
            return

        try:
            # Setup preview scene
            preview_obj, camera = self.preview_generator.setup_preview_scene()

            if not preview_obj or not camera:
                error_msg = (
                    "Failed to create preview scene. Check the console for errors."
                )
                self.status_bar.showMessage(error_msg)
                QtWidgets.QMessageBox.warning(self, "Preview Error", error_msg)
                return

            # Create temp directories if they don't exist
            temp_path = os.path.join(tempfile.gettempdir(), "houdini_material_previews")
            os.makedirs(temp_path, exist_ok=True)

            # Show progress dialog
            progress = QtWidgets.QProgressDialog(
                "Generating previews...", "Cancel", 0, len(self.materials), self
            )
            progress.setWindowModality(QtCore.Qt.WindowModal)

            # Counter for successful previews
            success_count = 0

            try:
                for i, material in enumerate(self.materials):
                    progress.setValue(i)
                    progress.setLabelText(f"Rendering preview for {material.name()}")

                    if progress.wasCanceled():
                        break

                    try:
                        # Check if material exists (don't use isValid as it's not available in all Houdini versions)
                        if not material.path() or not hou.node(material.path()):
                            print(f"Skipping invalid material: {material.name()}")
                            continue

                        # Generate preview
                        preview_path = self.preview_generator.generate_preview(
                            material, preview_obj, camera
                        )
                        if preview_path:
                            self.material_previews[material.path()] = preview_path
                            success_count += 1
                    except Exception as e:
                        print(
                            f"Error generating preview for {material.name()}: {str(e)}"
                        )
                        continue

                    # Force update the UI immediately
                    QtWidgets.QApplication.processEvents()

                # Rebuild the grid with the new previews
                self.populate_grid()

            finally:
                # Clean up preview scene
                self.preview_generator.cleanup_preview_scene(preview_obj, camera)
                progress.setValue(len(self.materials))

            # Show success/failure message
            if success_count == 0:
                error_msg = (
                    "Failed to generate any previews. Check the console for errors."
                )
                self.status_bar.showMessage(error_msg)
                QtWidgets.QMessageBox.warning(self, "Preview Error", error_msg)
            elif success_count < len(self.materials):
                status_msg = f"Generated {success_count} previews. {len(self.materials) - success_count} failed."
                self.status_bar.showMessage(status_msg)
                QtWidgets.QMessageBox.information(
                    self, "Preview Generation", status_msg
                )
            else:
                self.status_bar.showMessage(
                    f"Successfully generated all {success_count} previews."
                )

        except Exception as e:
            import traceback

            traceback.print_exc()
            error_msg = f"Error generating previews: {str(e)}"
            self.status_bar.showMessage(error_msg)
            QtWidgets.QMessageBox.critical(self, "Error", error_msg)

    def test_single_preview(self):
        """Test preview generation with a single material"""
        if not self.materials:
            self.status_bar.showMessage(
                "No materials to test. Please scan for materials first."
            )
            return

        # Pick the first material to test
        test_material = self.materials[0]

        # Show progress dialog
        progress = QtWidgets.QProgressDialog(
            "Testing preview generation...", "Cancel", 0, 2, self
        )
        progress.setWindowModality(QtCore.Qt.WindowModal)

        try:
            # Setup preview scene
            progress.setValue(0)
            progress.setLabelText("Setting up preview scene...")
            QtWidgets.QApplication.processEvents()

            preview_obj, camera = self.preview_generator.setup_preview_scene()

            if not preview_obj or not camera:
                error_msg = (
                    "Failed to create preview scene. Check the console for errors."
                )
                self.status_bar.showMessage(error_msg)
                QtWidgets.QMessageBox.warning(self, "Preview Error", error_msg)
                return

            # Generate test preview
            progress.setValue(1)
            progress.setLabelText(f"Generating test preview for {test_material.name()}")
            QtWidgets.QApplication.processEvents()

            preview_path = self.preview_generator.generate_preview(
                test_material, preview_obj, camera
            )

            if preview_path:
                self.material_previews[test_material.path()] = preview_path
                self.status_bar.showMessage(
                    f"Successfully generated test preview for {test_material.name()}"
                )

                # Update grid to show the test preview
                self.populate_grid()

                QtWidgets.QMessageBox.information(
                    self,
                    "Test Successful",
                    f"Successfully generated preview for {test_material.name()}\n\n"
                    "If this worked, you can now generate previews for all materials.",
                )
            else:
                self.status_bar.showMessage(
                    f"Failed to generate test preview for {test_material.name()}"
                )
                QtWidgets.QMessageBox.warning(
                    self,
                    "Test Failed",
                    f"Failed to generate preview for {test_material.name()}\n\n"
                    "Check the console for error messages and troubleshoot before trying to generate all previews.",
                )

            # Clean up preview scene
            self.preview_generator.cleanup_preview_scene(preview_obj, camera)

        except Exception as e:
            import traceback

            traceback.print_exc()
            error_msg = f"Error during test preview: {str(e)}"
            self.status_bar.showMessage(error_msg)
            QtWidgets.QMessageBox.critical(self, "Error", error_msg)

        progress.setValue(2)


def launch_material_browser():
    """Launch the material browser tool"""
    # Create and show the browser window
    browser = MaterialBrowserWidget(hou.ui.mainQtWindow())
    browser.show()

    # Initial scan for materials
    browser.scan_materials()

    # Return the browser instance to prevent it from being garbage collected
    return browser


# Store browser instance to prevent garbage collection
_browser_instance = None


def show_material_browser():
    """Show the material browser tool (creates a new instance if needed)"""
    global _browser_instance

    # If browser exists and is still valid, just show it
    if _browser_instance and not _browser_instance.isVisible():
        _browser_instance.show()
        _browser_instance.raise_()
        _browser_instance.activateWindow()
    else:
        # Create a new browser
        _browser_instance = launch_material_browser()

    return _browser_instance


def add_to_shelf():
    """Add the Material Browser tool to the current shelf"""
    # Get the current shelf set
    shelf_set = hou.ui.curDesktop().paneTabOfType(hou.paneTabType.ShelfTab).shellSet()

    # Check if we have any shelves
    if not shelf_set.shelves():
        return "No shelves found"

    # Create or find the Tools shelf
    tools_shelf = None
    for shelf in shelf_set.shelves():
        if shelf.name() == "tools":
            tools_shelf = shelf
            break

    if not tools_shelf:
        # Create a new Tools shelf if it doesn't exist
        tools_shelf = shelf_set.defaultShelf()

    # Create the tool
    tool = hou.shelftool.ShelfTool(
        "MaterialBrowser",
        "Material Browser",
        "Launch the Material Browser tool",
        icon="SHELF_material_palette",
    )

    tool.setScript(
        """
import inspect
import os
import sys

# Get the script directory path
script_path = os.path.dirname(inspect.getframeinfo(inspect.currentframe()).filename)

# Add the directory to sys.path if needed
if script_path not in sys.path:
    sys.path.append(script_path)

# Import the material browser module
import material_browser
import importlib
importlib.reload(material_browser)  # Reload to get latest changes

# Launch the browser
material_browser.show_material_browser()
"""
    )

    # Add the tool to the shelf
    tools_shelf.addTool(tool)

    return "Tool added to the shelf"


# Entry point for standalone use
if __name__ == "__main__":
    show_material_browser()
