import hou
import os
import re
from PySide2 import QtCore, QtWidgets
from .material_tool import RedshiftMaterialTool

class RedshiftMaterialToolDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super(RedshiftMaterialToolDialog, self).__init__(parent)
        self.setWindowTitle("Redshift Material Tool v2")
        self.resize(700, 500)

        # Default paths
        self.project_path = hou.text.expandString("$HIP")
        self.tex_path = os.path.join(self.project_path, "tex")

        # Create the material tool instance first
        self.material_tool = RedshiftMaterialTool()

        # Create the UI
        self.create_ui()

        # Set the default texture path in the UI
        if os.path.exists(self.tex_path):
            self.tex_path_field.setText(self.tex_path)
        else:
            # If the default texture path doesn't exist, just use the project path
            self.tex_path_field.setText(self.project_path)

        self.material_sets = {}
        self.checkbox_widgets = {}

    def create_ui(self):
        """Create the user interface"""
        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)

        # Texture directory selection
        tex_layout = QtWidgets.QHBoxLayout()
        tex_label = QtWidgets.QLabel("Texture Directory:")
        self.tex_path_field = QtWidgets.QLineEdit()
        self.tex_path_field.setText(self.tex_path)
        browse_button = QtWidgets.QPushButton("Browse...")
        browse_button.clicked.connect(self.browse_texture_directory)

        tex_layout.addWidget(tex_label)
        tex_layout.addWidget(self.tex_path_field, 1)
        tex_layout.addWidget(browse_button)

        layout.addLayout(tex_layout)

        # Add some spacing
        layout.addSpacing(10)

        # Options group box
        options_group = QtWidgets.QGroupBox("Options")
        options_layout = QtWidgets.QVBoxLayout()
        options_group.setLayout(options_layout)

        # Option to overwrite existing materials
        self.overwrite_checkbox = QtWidgets.QCheckBox("Overwrite existing materials")
        options_layout.addWidget(self.overwrite_checkbox)

        # Option to create a folder for each material
        self.create_folders_checkbox = QtWidgets.QCheckBox(
            "Create separate folder for each material"
        )
        options_layout.addWidget(self.create_folders_checkbox)

        layout.addWidget(options_group)

        # Material list section
        list_label = QtWidgets.QLabel("Materials to be created:")
        layout.addWidget(list_label)

        self.material_list = QtWidgets.QListWidget()
        layout.addWidget(self.material_list)

        # Scan button
        scan_button = QtWidgets.QPushButton("Scan for Textures")
        scan_button.clicked.connect(self.scan_textures)
        layout.addWidget(scan_button)

        # Buttons
        button_layout = QtWidgets.QHBoxLayout()
        create_button = QtWidgets.QPushButton("Create Materials")
        create_button.clicked.connect(self.create_materials)
        cancel_button = QtWidgets.QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)

        button_layout.addStretch()
        button_layout.addWidget(create_button)
        button_layout.addWidget(cancel_button)

        layout.addLayout(button_layout)
        # Add a group box for scan results with checkboxes
        self.scan_results_group = QtWidgets.QGroupBox("Scan Results")
        self.scan_results_layout = QtWidgets.QVBoxLayout()
        self.scan_results_group.setLayout(self.scan_results_layout)

        # Initially hide the scan results section
        self.scan_results_group.setVisible(False)

        # Add a scroll area for the checkboxes (in case there are many)
        scroll_area = QtWidgets.QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_widget = QtWidgets.QWidget()
        self.checkbox_layout = QtWidgets.QVBoxLayout(scroll_widget)
        scroll_area.setWidget(scroll_widget)
        self.scan_results_layout.addWidget(scroll_area)

        # Add buttons for controlling the checkboxes
        checkbox_buttons_layout = QtWidgets.QHBoxLayout()
        select_all_button = QtWidgets.QPushButton("Select All")
        select_all_button.clicked.connect(self.select_all_checkboxes)
        deselect_all_button = QtWidgets.QPushButton("Deselect All")
        deselect_all_button.clicked.connect(self.deselect_all_checkboxes)

        checkbox_buttons_layout.addWidget(select_all_button)
        checkbox_buttons_layout.addWidget(deselect_all_button)
        self.scan_results_layout.addLayout(checkbox_buttons_layout)

        # Add the scan results group to the main layout
        layout.addWidget(self.scan_results_group)

    def browse_texture_directory(self):
        """Open a directory browser to select the texture directory"""
        directory = QtWidgets.QFileDialog.getExistingDirectory(
            self, "Select Texture Directory", self.tex_path
        )

        if directory:
            self.tex_path = directory
            self.tex_path_field.setText(directory)

    def scan_textures(self):
        """Scan for textures and update the material list"""
        # Clear the material list
        self.material_list.clear()

        # Clear any existing checkboxes from previous scans
        if hasattr(self, "checkbox_layout"):
            self.clear_checkboxes()

        # Get and expand the texture path from the field
        input_path = self.tex_path_field.text()
        expanded_path = hou.text.expandString(input_path)

        # Update both paths in the material tool
        if os.path.exists(expanded_path):
            self.material_tool.tex_path = expanded_path

            # Adjust the project path based on the texture path
            # If the path ends with /tex, set project to parent dir
            if os.path.basename(expanded_path) == "tex":
                self.material_tool.project_path = os.path.dirname(expanded_path)
            else:
                # Otherwise, just use the directory as the project
                self.material_tool.project_path = expanded_path

            print(f"Scanning texture path: {expanded_path}")
            print(f"Using project path: {self.material_tool.project_path}")

            # Scan for textures
            material_sets = self.material_tool.scan_textures()

            if not material_sets:
                QtWidgets.QMessageBox.warning(
                    self,
                    "No Textures Found",
                    f"No texture sets found in:\n{expanded_path}\n\n"
                    f"Make sure your textures follow the expected naming conventions and folder structure.",
                )

                # Hide the scan results section if it exists
                if hasattr(self, "scan_results_group"):
                    self.scan_results_group.setVisible(False)

                return

            # Show the scan results group with checkboxes if it exists
            if hasattr(self, "scan_results_group"):
                self.scan_results_group.setVisible(True)

                # Add a checkbox for each mesh/material combination
                for mesh_name, materials in material_sets.items():
                    # Add a label for the mesh
                    mesh_label = QtWidgets.QLabel(f"<b>{mesh_name}</b>")
                    self.checkbox_layout.addWidget(mesh_label)

                    # Add checkboxes for each material
                    for material_name, textures in materials.items():
                        # Create a description of the material
                        texture_types = ", ".join(textures.keys())
                        checkbox_text = f"{material_name} ({len(textures)} textures: {texture_types})"

                        # Create the checkbox
                        checkbox = QtWidgets.QCheckBox(checkbox_text)
                        checkbox.setChecked(True)  # Default to checked

                        # Store the checkbox with a unique key
                        key = f"{mesh_name}:{material_name}"
                        self.checkbox_widgets[key] = checkbox

                        # Add the checkbox to the layout
                        self.checkbox_layout.addWidget(checkbox)

                    # Add a spacer after each mesh
                    spacer = QtWidgets.QSpacerItem(
                        20,
                        10,
                        QtWidgets.QSizePolicy.Minimum,
                        QtWidgets.QSizePolicy.Fixed,
                    )
                    self.checkbox_layout.addSpacerItem(spacer)

                # Store the material sets for later use
                self.material_sets = material_sets

                # Show a summary
                QtWidgets.QMessageBox.information(
                    self,
                    "Scan Complete",
                    f"Found {len(self.checkbox_widgets)} materials in {len(self.material_sets)} mesh folders.",
                )
            else:
                # Original behavior - populate the list widget
                for mesh_name, materials in material_sets.items():
                    for material_name, textures in materials.items():
                        # Create a descriptive display string
                        texture_types = ", ".join(textures.keys())
                        item_text = f"{mesh_name} / {material_name} ({len(textures)} textures: {texture_types})"

                        # Create a list item with the complete material data
                        item = QtWidgets.QListWidgetItem(item_text)
                        item.setData(
                            QtCore.Qt.UserRole,
                            {
                                "mesh_name": mesh_name,
                                "material_name": material_name,
                                "textures": textures,  # Contains ALL textures for this material
                            },
                        )
                        self.material_list.addItem(item)

                print(f"Found {self.material_list.count()} consolidated materials")
        else:
            QtWidgets.QMessageBox.warning(
                self,
                "Invalid Directory",
                f"The specified directory does not exist:\n{expanded_path}",
            )

    def extract_base_material_name(self, material_name):
        """Extract a clean base material name without texture type indicators"""
        # Remove UDIM tags
        clean_name = material_name.replace("<UDIM>", "")
        clean_name = clean_name.replace("%(UDIM)d", "")

        # Handle BarBase_Bar_combo_Color.UDIM format
        for suffix in [
            "Color",
            "DisplaceHeightField",
            "EmissionColor",
            "Metalness",
            "Normal",
            "Roughness",
            "alpha",
            "translucency",
            "AO",
            "height",
            "basecolor",
            "diffuse",
            "albedo",
            "roughness",
            "rough",
            "metallic",
            "metal",
            "normal",
            "bump",
            "displacement",
            "emission",
            "ao",
        ]:

            # Check for suffix at end with dot or underscore
            if re.search(rf"[_\.]({re.escape(suffix)})$", clean_name, re.IGNORECASE):
                clean_name = re.sub(
                    rf"[_\.]({re.escape(suffix)})$", "", clean_name, flags=re.IGNORECASE
                )
                break

            # Check for suffix in middle with separators
            if re.search(
                rf"[_\.]({re.escape(suffix)})[_\.]", clean_name, re.IGNORECASE
            ):
                clean_name = re.sub(
                    rf"[_\.]({re.escape(suffix)})[_\.]",
                    "",
                    clean_name,
                    flags=re.IGNORECASE,
                )
                break

        # Remove trailing separators
        clean_name = re.sub(r"[_\.]+$", "", clean_name)

        return clean_name

    def create_materials(self):
        """Create the materials based on the selected items in the list or checkboxes"""
        # Determine if we're using checkboxes or the list widget
        using_checkboxes = hasattr(self, "checkbox_widgets") and self.checkbox_widgets

        # Check if we have materials
        if using_checkboxes and not hasattr(self, "material_sets"):
            QtWidgets.QMessageBox.warning(
                self,
                "No Materials",
                "No materials found. Please scan for textures first.",
            )
            return
        elif not using_checkboxes and self.material_list.count() == 0:
            QtWidgets.QMessageBox.warning(
                self,
                "No Materials",
                "No materials found. Please scan for textures first.",
            )
            return

        # Get the material context
        try:
            mat_context = self.material_tool.create_material_context()
        except Exception as e:
            QtWidgets.QMessageBox.critical(
                self, "Error", f"Failed to create material context: {str(e)}"
            )
            return

        # Process materials based on UI type (checkboxes or list)
        if using_checkboxes:
            # Create a list of materials to create based on checked boxes
            materials_to_create = []
            for key, checkbox in self.checkbox_widgets.items():
                if checkbox.isChecked():
                    mesh_name, material_name = key.split(":", 1)
                    materials_to_create.append(
                        {
                            "mesh_name": mesh_name,
                            "material_name": material_name,
                            "textures": self.material_sets[mesh_name][material_name],
                        }
                    )

            if not materials_to_create:
                QtWidgets.QMessageBox.warning(
                    self,
                    "No Selection",
                    "No materials selected. Please select at least one material.",
                )
                return
        else:
            # Process selected materials from the list or all if none selected
            selected_items = self.material_list.selectedItems()
            if not selected_items:
                # No selection, process all
                material_items = [
                    self.material_list.item(i)
                    for i in range(self.material_list.count())
                ]
            else:
                material_items = selected_items

            # Convert to the same format as the checkbox version
            materials_to_create = [
                item.data(QtCore.Qt.UserRole) for item in material_items
            ]

        # Create materials
        created_count = 0
        skipped_count = 0

        progress = QtWidgets.QProgressDialog(
            "Creating materials...", "Cancel", 0, len(materials_to_create), self
        )
        progress.setWindowModality(QtCore.Qt.WindowModal)

        for i, material_data in enumerate(materials_to_create):
            progress.setValue(i)
            if progress.wasCanceled():
                break

            mesh_name = material_data["mesh_name"]
            material_name = material_data["material_name"]
            textures = material_data["textures"]

            # Check if material already exists
            existing_mat = self.material_tool.check_material_exists(
                mat_context, material_name
            )

            if existing_mat and not self.overwrite_checkbox.isChecked():
                progress.setLabelText(f"Skipping existing material: {material_name}")
                skipped_count += 1
                continue

            # Delete existing material if we're overwriting
            if existing_mat and self.overwrite_checkbox.isChecked():
                existing_mat.destroy()

            try:
                # Create new material
                if self.create_folders_checkbox.isChecked():
                    # Create a subnet for this material
                    material_folder = mat_context.createNode(
                        "subnet", f"FOLDER_{material_name}"
                    )
                    new_mat = self.material_tool.create_redshift_material(
                        material_folder, material_name, textures
                    )
                else:
                    new_mat = self.material_tool.create_redshift_material(
                        mat_context, material_name, textures
                    )

                if new_mat:
                    progress.setLabelText(f"Created material: {material_name}")
                    created_count += 1
            except Exception as e:
                progress.setLabelText(f"Error creating {material_name}: {str(e)}")

        progress.setValue(len(materials_to_create))

        # Layout nodes in material context
        try:
            mat_context.layoutChildren()
        except Exception as e:
            print(f"Warning: Could not layout children: {str(e)}")

        # Show summary
        QtWidgets.QMessageBox.information(
            self,
            "Material Creation Complete",
            f"Created {created_count} new materials\nSkipped {skipped_count} existing materials",
        )

        # Close the dialog if successful
        if created_count > 0:
            self.accept()

    def select_all_checkboxes(self):
        """Select all checkboxes"""
        for checkbox in self.checkbox_widgets.values():
            checkbox.setChecked(True)

    def deselect_all_checkboxes(self):
        """Deselect all checkboxes"""
        for checkbox in self.checkbox_widgets.values():
            checkbox.setChecked(False)

    def clear_checkboxes(self):
        """Clear all checkboxes from the layout"""
        # Remove all existing checkboxes
        for i in reversed(range(self.checkbox_layout.count())):
            widget = self.checkbox_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()

        self.checkbox_widgets = {}


# Function to launch the dialog
def create_redshift_material_tool_v2():
    """Launch the Redshift Material Tool v2 dialog"""
    dialog = RedshiftMaterialToolDialog(hou.ui.mainQtWindow())
    dialog.exec_()


# For testing the tool in Houdini
if __name__ == "__main__":
    create_redshift_material_tool_v2()
