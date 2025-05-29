"""
Weapon Part Upload Widget
-----------------------
UI widget for uploading new weapon parts to the API.
"""

from PySide2 import QtCore, QtWidgets
import os
import threading


class WeaponPartUploadWidget(QtWidgets.QWidget):
    """Widget for uploading new weapon parts to the API"""

    uploadCompleted = QtCore.Signal(bool, str)
    progressUpdated = QtCore.Signal(int)

    def __init__(self, parent=None, api=None):
        super().__init__(parent)
        self.api = api
        self.model_path = ""
        self.icon_path = ""
        self.create_ui()

    def create_ui(self):
        """Create the upload UI layout"""
        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)

        # Weapon type selection
        weapon_layout = QtWidgets.QHBoxLayout()
        weapon_layout.addWidget(QtWidgets.QLabel("Weapon Type:"))
        self.weapon_type_combo = QtWidgets.QComboBox()
        self.weapon_type_combo.currentIndexChanged.connect(self.on_weapon_type_changed)
        weapon_layout.addWidget(self.weapon_type_combo)
        layout.addLayout(weapon_layout)

        # Part type selection
        part_layout = QtWidgets.QHBoxLayout()
        part_layout.addWidget(QtWidgets.QLabel("Part Type:"))
        self.part_type_combo = QtWidgets.QComboBox()
        part_layout.addWidget(self.part_type_combo)
        layout.addLayout(part_layout)

        # Model file selection
        model_layout = QtWidgets.QHBoxLayout()
        model_layout.addWidget(QtWidgets.QLabel("Model File:"))
        self.model_path_edit = QtWidgets.QLineEdit()
        self.model_path_edit.setReadOnly(True)
        model_browse = QtWidgets.QPushButton("Browse...")
        model_browse.clicked.connect(self.browse_model_file)
        model_layout.addWidget(self.model_path_edit)
        model_layout.addWidget(model_browse)
        layout.addLayout(model_layout)

        # Icon file selection
        icon_layout = QtWidgets.QHBoxLayout()
        icon_layout.addWidget(QtWidgets.QLabel("Icon File:"))
        self.icon_path_edit = QtWidgets.QLineEdit()
        self.icon_path_edit.setReadOnly(True)
        icon_browse = QtWidgets.QPushButton("Browse...")
        icon_browse.clicked.connect(self.browse_icon_file)
        icon_layout.addWidget(self.icon_path_edit)
        icon_layout.addWidget(icon_browse)
        layout.addLayout(icon_layout)

        # Progress bar
        self.progress_bar = QtWidgets.QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        # Action buttons
        button_layout = QtWidgets.QHBoxLayout()
        self.upload_button = QtWidgets.QPushButton("Upload Part")
        self.upload_button.clicked.connect(self.upload_part)
        self.cancel_button = QtWidgets.QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.cancel_upload)
        button_layout.addWidget(self.upload_button)
        button_layout.addWidget(self.cancel_button)
        layout.addLayout(button_layout)

        # Load initial weapon types
        self.populate_weapon_types()

    def populate_weapon_types(self):
        """Populate the weapon type combo box"""
        if not self.api:
            return

        self.weapon_type_combo.clear()
        weapon_types = self.api.get_weapon_types()
        self.weapon_type_combo.addItems(weapon_types)

    def populate_part_types(self, weapon_type):
        """Populate the part type combo box based on weapon type"""
        if not self.api:
            return

        self.part_type_combo.clear()
        part_types = self.api.get_part_types(weapon_type)
        self.part_type_combo.addItems(part_types)

    def on_weapon_type_changed(self, index):
        """Handle weapon type selection change"""
        if index < 0:
            return

        weapon_type = self.weapon_type_combo.currentText()
        self.populate_part_types(weapon_type)

    def browse_model_file(self):
        """Open file dialog to select model file"""
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "Select Model File",
            "",
            "3D Model Files (*.fbx *.obj *.gltf *.glb);;All Files (*.*)",
        )
        if file_path:
            self.model_path = file_path
            self.model_path_edit.setText(os.path.basename(file_path))

    def browse_icon_file(self):
        """Open file dialog to select icon file"""
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "Select Icon File",
            "",
            "Image Files (*.png *.jpg *.jpeg);;All Files (*.*)",
        )
        if file_path:
            self.icon_path = file_path
            self.icon_path_edit.setText(os.path.basename(file_path))

    def upload_part(self):
        """Upload the weapon part to the API"""
        if not self.api:
            return

        # Validate inputs
        if not self.model_path:
            QtWidgets.QMessageBox.warning(
                self, "Missing Model", "Please select a model file."
            )
            return

        if not self.icon_path:
            QtWidgets.QMessageBox.warning(
                self, "Missing Icon", "Please select an icon file."
            )
            return

        weapon_type = self.weapon_type_combo.currentText()
        part_type = self.part_type_combo.currentText()

        if not weapon_type or not part_type:
            QtWidgets.QMessageBox.warning(
                self, "Missing Type", "Please select both weapon type and part type."
            )
            return

        # Prepare metadata
        metadata = {
            "weapon_type": weapon_type,
            "part_type": part_type,
            "name": os.path.splitext(os.path.basename(self.model_path))[0],
        }

        # Show progress and disable buttons
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.upload_button.setEnabled(False)
        self.cancel_button.setEnabled(True)

        # Start upload in a separate thread
        threading.Thread(
            target=self._do_upload,
            args=(self.model_path, self.icon_path, metadata, self.progress_bar),
        ).start()

    def cancel_upload(self):
        """Cancel the current upload"""
        # TODO: Implement upload cancellation
        pass

    def on_upload_completed(self, success, message):
        """Handle upload completion"""
        self.progress_bar.setVisible(False)
        self.upload_button.setEnabled(True)
        self.cancel_button.setEnabled(False)

        if success:
            QtWidgets.QMessageBox.information(
                self,
                "Upload Successful",
                "The weapon part has been uploaded successfully.",
            )
            self.clear_form()
        else:
            QtWidgets.QMessageBox.critical(
                self, "Upload Failed", f"Failed to upload weapon part: {message}"
            )

    def _do_upload(self, model_path, icon_path, metadata, progress):
        """Perform the upload in a separate thread"""
        try:
            # Simulate progress updates
            for i in range(101):
                QtCore.QMetaObject.invokeMethod(
                    progress,
                    "setValue",
                    QtCore.Qt.QueuedConnection,
                    QtCore.Q_ARG(int, i),
                )
                QtCore.QThread.msleep(50)  # Simulate work

            # Upload the model
            result = self.api.upload_model(model_path, icon_path, metadata)

            if result:
                QtCore.QMetaObject.invokeMethod(
                    self,
                    "on_upload_completed",
                    QtCore.Qt.QueuedConnection,
                    QtCore.Q_ARG(bool, True),
                )
            else:
                QtCore.QMetaObject.invokeMethod(
                    self,
                    "on_upload_completed",
                    QtCore.Qt.QueuedConnection,
                    QtCore.Q_ARG(bool, False),
                    QtCore.Q_ARG(str, "Upload failed"),
                )
        except Exception as e:
            QtCore.QMetaObject.invokeMethod(
                self,
                "on_upload_completed",
                QtCore.Qt.QueuedConnection,
                QtCore.Q_ARG(bool, False),
                QtCore.Q_ARG(str, str(e)),
            )

    def clear_form(self):
        """Clear all form fields"""
        self.model_path = ""
        self.icon_path = ""
        self.model_path_edit.clear()
        self.icon_path_edit.clear()
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
