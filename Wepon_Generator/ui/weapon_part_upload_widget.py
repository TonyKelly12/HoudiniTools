"""
Weapon Part Upload Widget
-----------------------
UI widget for uploading new weapon parts to the API.
"""

from PySide2 import QtCore, QtWidgets, QtGui

import os
import threading
from .weapon_assembly import WeaponAssemblyAPI


class WeaponPartUploadWidget(QtWidgets.QWidget):
    """Widget for uploading new weapon parts to the API"""

    uploadCompleted = QtCore.Signal(bool, str)
    progressUpdated = QtCore.Signal(int)

    def __init__(self, parent=None, api=None):
        super(WeaponPartUploadWidget, self).__init__(parent)
        self.api = api  # Share the API client with the main widget

        # Create the UI
        self.create_ui()

        # Connect signals
        self.uploadCompleted.connect(self.on_upload_completed)

    def create_ui(self):
        """Create the upload form UI"""
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # Create scrollable area for the form
        scroll_area = QtWidgets.QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QtWidgets.QFrame.NoFrame)

        form_widget = QtWidgets.QWidget()
        form_layout = QtWidgets.QFormLayout(form_widget)
        form_layout.setFieldGrowthPolicy(QtWidgets.QFormLayout.AllNonFixedFieldsGrow)

        # Basic information section
        form_layout.addRow(QtWidgets.QLabel("<b>Basic Information</b>"))

        # Part name
        self.name_input = QtWidgets.QLineEdit()
        self.name_input.setPlaceholderText("Enter a name for this part")
        form_layout.addRow("Name:", self.name_input)

        # Description
        self.description_input = QtWidgets.QTextEdit()
        self.description_input.setPlaceholderText("Enter a description of the part")
        self.description_input.setMaximumHeight(80)
        form_layout.addRow("Description:", self.description_input)

        # Tags
        self.tags_input = QtWidgets.QLineEdit()
        self.tags_input.setPlaceholderText("Enter tags separated by commas")
        form_layout.addRow("Tags:", self.tags_input)

        # Category
        self.category_input = QtWidgets.QLineEdit()
        self.category_input.setPlaceholderText("Enter category (e.g., weapons)")
        self.category_input.setText("weapons")  # Default
        form_layout.addRow("Category:", self.category_input)

        # Weapon part section
        form_layout.addRow(QtWidgets.QLabel("<b>Weapon Part Details</b>"))

        # Is weapon part checkbox
        self.is_weapon_part = QtWidgets.QCheckBox("This is a weapon part")
        self.is_weapon_part.setChecked(True)  # Default
        form_layout.addRow("", self.is_weapon_part)

        # Weapon type
        self.weapon_type_combo = QtWidgets.QComboBox()
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
        for weapon_type in weapon_types:
            self.weapon_type_combo.addItem(weapon_type.capitalize(), weapon_type)
        form_layout.addRow("Weapon Type:", self.weapon_type_combo)

        # Part type
        self.part_type_combo = QtWidgets.QComboBox()
        # We'll populate this dynamically based on weapon type
        self.populate_part_types("sword")  # Default
        form_layout.addRow("Part Type:", self.part_type_combo)

        # Connect weapon type change to update part types
        self.weapon_type_combo.currentIndexChanged.connect(self.on_weapon_type_changed)

        # Material slots
        self.material_slots_input = QtWidgets.QLineEdit()
        self.material_slots_input.setPlaceholderText(
            "Enter material slot names separated by commas"
        )
        form_layout.addRow("Material Slots:", self.material_slots_input)

        # Variant information
        form_layout.addRow(QtWidgets.QLabel("<b>Variant Information (Optional)</b>"))

        # Variant name
        self.variant_name_input = QtWidgets.QLineEdit()
        self.variant_name_input.setPlaceholderText(
            "Enter variant name (e.g., ornate, rusty)"
        )
        form_layout.addRow("Variant Name:", self.variant_name_input)

        # Variant group
        self.variant_group_input = QtWidgets.QLineEdit()
        self.variant_group_input.setPlaceholderText(
            "Enter variant group (e.g., materials, styles)"
        )
        form_layout.addRow("Variant Group:", self.variant_group_input)

        # File upload section
        form_layout.addRow(QtWidgets.QLabel("<b>Files</b>"))

        # Model file
        model_layout = QtWidgets.QHBoxLayout()
        self.model_path_label = QtWidgets.QLineEdit()
        self.model_path_label.setReadOnly(True)
        self.model_path_label.setPlaceholderText("No file selected")

        self.browse_model_button = QtWidgets.QPushButton("Browse...")
        self.browse_model_button.clicked.connect(self.browse_model_file)

        model_layout.addWidget(self.model_path_label)
        model_layout.addWidget(self.browse_model_button)

        form_layout.addRow("Model File:", model_layout)

        # Icon/Preview file
        icon_layout = QtWidgets.QHBoxLayout()
        self.icon_path_label = QtWidgets.QLineEdit()
        self.icon_path_label.setReadOnly(True)
        self.icon_path_label.setPlaceholderText("No file selected")

        self.browse_icon_button = QtWidgets.QPushButton("Browse...")
        self.browse_icon_button.clicked.connect(self.browse_icon_file)

        icon_layout.addWidget(self.icon_path_label)
        icon_layout.addWidget(self.browse_icon_button)

        form_layout.addRow("Icon/Preview:", icon_layout)

        # Preview area for icon
        self.preview_label = QtWidgets.QLabel()
        self.preview_label.setMinimumSize(150, 150)
        self.preview_label.setMaximumSize(150, 150)
        self.preview_label.setAlignment(QtCore.Qt.AlignCenter)
        self.preview_label.setStyleSheet(
            "background-color: #333333; border: 1px solid #555555;"
        )
        self.preview_label.setText("No preview")

        preview_layout = QtWidgets.QHBoxLayout()
        preview_layout.addStretch()
        preview_layout.addWidget(self.preview_label)
        preview_layout.addStretch()

        form_layout.addRow("", preview_layout)

        # Set the form widget as the scrollable content
        scroll_area.setWidget(form_widget)
        main_layout.addWidget(scroll_area)

        # Add upload button
        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addStretch()

        self.upload_button = QtWidgets.QPushButton("Upload Part")
        self.upload_button.setMinimumWidth(120)
        self.upload_button.setMinimumHeight(40)
        self.upload_button.clicked.connect(self.upload_part)

        button_layout.addWidget(self.upload_button)

        main_layout.addLayout(button_layout)

    def populate_part_types(self, weapon_type):
        """Populate part types based on weapon type"""
        self.part_type_combo.clear()

        common_parts = ["handle", "grip"]

        part_types = {
            "sword": common_parts + ["blade", "guard", "pommel"],
            "axe": common_parts + ["head"],
            "mace": common_parts + ["head"],
            "bow": common_parts + ["limbs", "string"],
            "spear": common_parts + ["shaft", "head"],
            "dagger": common_parts + ["blade", "guard"],
            "staff": common_parts + ["shaft", "head"],
            "shield": ["body", "border", "boss"],
            "gun": ["handle", "barrel", "trigger", "magazine", "sight"],
            "rifle": ["stock", "barrel", "trigger", "magazine", "sight"],
            "custom": ["handle", "body", "custom"],
        }

        for part_type in part_types.get(weapon_type.lower(), common_parts):
            self.part_type_combo.addItem(part_type.capitalize(), part_type)

    def on_weapon_type_changed(self, index):
        """Handle weapon type selection change"""
        if index < 0:
            return

        weapon_type = self.weapon_type_combo.itemData(index)
        self.populate_part_types(weapon_type)

    def browse_model_file(self):
        """Open file browser to select model file"""
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "Select Model File",
            "",
            "3D Models (*.fbx *.obj *.usd *.usda *.usdc *.usdz *.glb *.gltf);;All Files (*)",
        )

        if file_path:
            self.model_path_label.setText(file_path)

    def browse_icon_file(self):
        """Open file browser to select icon/preview file"""
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "Select Icon/Preview Image",
            "",
            "Images (*.png *.jpg *.jpeg);;All Files (*)",
        )

        if file_path:
            self.icon_path_label.setText(file_path)

            # Update preview
            pixmap = QtGui.QPixmap(file_path)
            if not pixmap.isNull():
                pixmap = pixmap.scaled(
                    150, 150, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation
                )
                self.preview_label.setPixmap(pixmap)
            else:
                self.preview_label.setText("Invalid image")

    def upload_part(self):
        """Upload the part to the API"""
        # Validate required fields
        if not self.name_input.text().strip():
            QtWidgets.QMessageBox.warning(
                self, "Missing Information", "Please enter a name for the part."
            )
            return

        if not self.model_path_label.text():
            QtWidgets.QMessageBox.warning(
                self, "Missing File", "Please select a model file to upload."
            )
            return

        if not self.icon_path_label.text():
            QtWidgets.QMessageBox.warning(
                self, "Missing File", "Please select an icon/preview image."
            )
            return

        # Prepare metadata
        tags = [tag.strip() for tag in self.tags_input.text().split(",") if tag.strip()]

        material_slots = None
        if self.material_slots_input.text().strip():
            material_slots = [
                slot.strip()
                for slot in self.material_slots_input.text().split(",")
                if slot.strip()
            ]

        # Prepare weapon part metadata
        weapon_part_metadata = None
        if self.is_weapon_part.isChecked():
            weapon_part_metadata = {
                "weapon_type": self.weapon_type_combo.currentData(),
                "part_type": self.part_type_combo.currentData(),
                "is_attachment": False,
                "material_slots": material_slots,
            }

            # Add variant info if provided
            if self.variant_name_input.text().strip():
                weapon_part_metadata["variant_name"] = (
                    self.variant_name_input.text().strip()
                )

            if self.variant_group_input.text().strip():
                weapon_part_metadata["variant_group"] = (
                    self.variant_group_input.text().strip()
                )

        # Prepare metadata JSON
        metadata = {
            "name": self.name_input.text().strip(),
            "description": self.description_input.toPlainText().strip(),
            "format": os.path.splitext(self.model_path_label.text())[1][1:].lower(),
            "category": self.category_input.text().strip() or "weapons",
            "is_weapon_part": self.is_weapon_part.isChecked(),
        }

        if tags:
            metadata["tags"] = tags

        if weapon_part_metadata:
            metadata["weapon_part_metadata"] = weapon_part_metadata

        # Disable UI during upload
        self.setEnabled(False)

        # Show progress dialog
        self.progress_dialog = QtWidgets.QProgressDialog(
            "Uploading weapon part...", "Cancel", 0, 100, self
        )
        self.progress_dialog.setWindowModality(QtCore.Qt.WindowModal)
        self.progress_dialog.setMinimumDuration(0)
        self.progress_dialog.setValue(10)
        self.progress_dialog.canceled.connect(self.cancel_upload)

        # Connect progress signal to update dialog
        self.progressUpdated.connect(self.progress_dialog.setValue)

        # Start upload in a background thread
        self.upload_thread = threading.Thread(
            target=self._do_upload,
            args=(
                self.model_path_label.text(),
                self.icon_path_label.text(),
                metadata,
                self.progress_dialog,
            ),
        )
        self.upload_thread.daemon = True
        self.upload_thread.start()

    def cancel_upload(self):
        """Handle user cancellation of upload"""
        # Signal cancellation to the user
        self.uploadCompleted.emit(False, "Upload cancelled by user")

    def on_upload_completed(self, success, message):
        """Handle upload completion - triggered from signal"""
        # Re-enable UI
        self.setEnabled(True)

        # Close progress dialog if it exists
        if hasattr(self, "progress_dialog") and self.progress_dialog:
            self.progress_dialog.close()

        if success:
            # Show success message
            QtWidgets.QMessageBox.information(
                self,
                "Upload Complete",
                message
                + "\n\nThe part has been added to the database and will appear in the parts list.",
            )

            # Clear form for next upload
            self.clear_form()
        else:
            # Show error message
            QtWidgets.QMessageBox.warning(self, "Upload Failed", message)

    def _do_upload(self, model_path, icon_path, metadata, progress):
        """Perform the upload in a background thread with better logging"""
        try:
            print("Starting upload process...")

            # Update progress
            self.progressUpdated.emit(10)
            print("Progress: 10% - Starting file preparation")

            # Check if files exist
            if not os.path.exists(model_path):
                print(f"Error: Model file not found: {model_path}")
                self.uploadCompleted.emit(False, f"Model file not found: {model_path}")
                return

            if not os.path.exists(icon_path):
                print(f"Error: Icon file not found: {icon_path}")
                self.uploadCompleted.emit(False, f"Icon file not found: {icon_path}")
                return

            # Remove any icon_path field from metadata to prevent errors
            if "icon_path" in metadata:
                del metadata["icon_path"]

            try:
                # Try opening the files to ensure they're accessible
                model_size = os.path.getsize(model_path)
                print(f"Model file opened successfully. Size: {model_size} bytes")

                icon_size = os.path.getsize(icon_path)
                print(f"Icon file opened successfully. Size: {icon_size} bytes")
            except Exception as file_error:
                print(f"File access error: {str(file_error)}")
                self.uploadCompleted.emit(
                    False, f"File access error: {str(file_error)}"
                )
                return

            # Update progress
            self.progressUpdated.emit(20)
            print("Progress: 20% - Files prepared, creating request")

            import requests
            import json

            # Convert metadata to JSON
            metadata_json = json.dumps(metadata)
            print(f"Metadata JSON prepared: {metadata_json[:100]}...")

            # Build URL
            if self.api and hasattr(self.api, "base_url"):
                url = f"{self.api.base_url}/models/"
                print(f"Target URL: {url}")
            else:
                print("Error: API client not available or missing base_url")
                self.uploadCompleted.emit(False, "API client not available")
                return

            # Update progress
            self.progressUpdated.emit(30)
            print("Progress: 30% - Request prepared, opening files for upload")

            try:
                # Prepare files with explicit mode and proper closure
                model_file = open(model_path, "rb")
                icon_file = open(icon_path, "rb")

                files = {
                    "file": (
                        os.path.basename(model_path),
                        model_file,
                        "application/octet-stream",
                    ),
                    "icon": (os.path.basename(icon_path), icon_file, "image/png"),
                }

                data = {"metadata_json": metadata_json}

                # Update progress
                self.progressUpdated.emit(40)
                print("Progress: 40% - Files opened, sending request")

                # Set timeout to prevent hanging forever
                try:
                    print("Sending POST request...")
                    response = requests.post(url, files=files, data=data, timeout=120)
                    print(f"Request completed with status code: {response.status_code}")

                    # Update progress
                    self.progressUpdated.emit(90)
                    print("Progress: 90% - Request completed, processing response")

                    if response.status_code == 200:
                        try:
                            result = response.json()
                            print(f"Response JSON: {result}")
                            self.uploadCompleted.emit(
                                True, f"Part ID: {result.get('id', 'unknown')}"
                            )
                        except Exception as json_error:
                            print(f"Error parsing response JSON: {str(json_error)}")
                            print(f"Response text: {response.text[:500]}")
                            self.uploadCompleted.emit(
                                False, f"Error parsing response: {str(json_error)}"
                            )
                    else:
                        print(
                            f"Error response: {response.status_code} - {response.text[:500]}"
                        )
                        self.uploadCompleted.emit(
                            False,
                            f"Upload failed with status {response.status_code}: {response.text[:200]}",
                        )
                except requests.exceptions.Timeout:
                    print("Request timed out after 120 seconds")
                    self.uploadCompleted.emit(False, "Request timed out (2 minutes)")
                except requests.exceptions.ConnectionError as conn_error:
                    print(f"Connection error: {str(conn_error)}")
                    self.uploadCompleted.emit(
                        False, f"Connection error: {str(conn_error)}"
                    )
                except Exception as req_error:
                    print(f"Request error: {str(req_error)}")
                    self.uploadCompleted.emit(False, f"Request error: {str(req_error)}")
                finally:
                    # Ensure files are closed
                    model_file.close()
                    icon_file.close()
                    print("Files closed")

            except Exception as file_open_error:
                print(f"Error opening files for upload: {str(file_open_error)}")
                self.uploadCompleted.emit(
                    False, f"Error opening files: {str(file_open_error)}"
                )

        except Exception as e:
            import traceback

            print("Exception in upload process:")
            traceback.print_exc()
            self.uploadCompleted.emit(False, f"Upload error: {str(e)}")
        finally:
            # Ensure progress is completed in all cases
            self.progressUpdated.emit(100)
            print("Upload process completed")

    def clear_form(self):
        """Clear the form fields after successful upload"""
        self.name_input.clear()
        self.description_input.clear()
        self.tags_input.clear()
        self.category_input.setText("weapons")
        self.material_slots_input.clear()
        self.variant_name_input.clear()
        self.variant_group_input.clear()
        self.model_path_label.clear()
        self.icon_path_label.clear()
        self.preview_label.setPixmap(QtGui.QPixmap())
        self.preview_label.setText("No preview")
