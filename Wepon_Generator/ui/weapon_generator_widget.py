"""
Weapon Generator Widget
---------------------
Main UI widget for the weapon generator interface.
"""

import hou
from PySide2 import QtCore, QtWidgets, QtGui
from PySide2.QtNetwork import QNetworkAccessManager, QNetworkReply
import threading


from ..api.weapon_assembly_api import WeaponAssemblyAPI


class WeaponGeneratorWidget(QtWidgets.QWidget):
    """Widget for the Weapon Generator UI"""

    # Signal definitions
    connectionStatusChanged = QtCore.Signal(bool)
    partsLoaded = QtCore.Signal(str, object)
    generationFinished = QtCore.Signal(bool, str)
    weaponAssembled = QtCore.Signal(object, object)
    progressUpdated = QtCore.Signal(int)
    refreshRequested = QtCore.Signal()

    def __init__(self, parent=None, node_path=None):
        super().__init__(parent)
        self.node_path = node_path
        self.api = WeaponAssemblyAPI()
        self.network_manager = QNetworkAccessManager()
        self.network_manager.finished.connect(self.handle_network_response)
        self.current_page = 1
        self.selected_parts = {}
        self.create_ui()
        self.initialize()

    def update_progress(self, value):
        """Update the progress bar value"""
        self.progress_bar.setValue(value)

    def create_ui(self):
        """Create the main UI layout"""
        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)

        # Connection status
        status_layout = QtWidgets.QHBoxLayout()
        self.status_label = QtWidgets.QLabel("Status: Checking connection...")
        self.test_button = QtWidgets.QPushButton("Test Connection")
        self.test_button.clicked.connect(self.test_connection)
        status_layout.addWidget(self.status_label)
        status_layout.addWidget(self.test_button)
        layout.addLayout(status_layout)

        # Weapon type selection
        weapon_layout = QtWidgets.QHBoxLayout()
        weapon_layout.addWidget(QtWidgets.QLabel("Weapon Type:"))
        self.weapon_type_combo = QtWidgets.QComboBox()
        self.weapon_type_combo.currentIndexChanged.connect(self.on_weapon_type_changed)
        weapon_layout.addWidget(self.weapon_type_combo)
        layout.addLayout(weapon_layout)

        # Parts selection area
        self.parts_scroll = QtWidgets.QScrollArea()
        self.parts_scroll.setWidgetResizable(True)
        self.parts_widget = QtWidgets.QWidget()
        self.parts_layout = QtWidgets.QVBoxLayout()
        self.parts_widget.setLayout(self.parts_layout)
        self.parts_scroll.setWidget(self.parts_widget)
        layout.addWidget(self.parts_scroll)

        # Progress bar
        self.progress_bar = QtWidgets.QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        # Action buttons
        button_layout = QtWidgets.QHBoxLayout()
        self.generate_button = QtWidgets.QPushButton("Generate Weapon")
        self.generate_button.clicked.connect(self.generate_weapon)
        self.reset_button = QtWidgets.QPushButton("Reset Selection")
        self.reset_button.clicked.connect(self.reset_selection)
        button_layout.addWidget(self.generate_button)
        button_layout.addWidget(self.reset_button)
        layout.addLayout(button_layout)

    def initialize(self):
        """Initialize the widget"""
        self.load_weapon_types()
        self.test_connection()

    def test_connection(self):
        """Test the connection to the API"""
        self.test_button.setEnabled(False)
        self.status_label.setText("Status: Testing connection...")
        threading.Thread(target=self._run_test).start()

    def _run_test(self):
        """Run the connection test in a separate thread"""
        connected = self.api.test_connection()
        QtCore.QMetaObject.invokeMethod(
            self,
            "update_connection_status",
            QtCore.Qt.QueuedConnection,
            QtCore.Q_ARG(bool, connected),
        )

    def update_connection_status(self, connected):
        """Update the connection status display"""
        self.test_button.setEnabled(True)
        if connected:
            self.status_label.setText("Status: Connected")
            self.status_label.setStyleSheet("color: green")
        else:
            self.status_label.setText("Status: Disconnected")
            self.status_label.setStyleSheet("color: red")

    def load_weapon_types(self):
        """Load available weapon types into the combo box"""
        self.weapon_type_combo.clear()
        weapon_types = self.api.get_weapon_types()
        self.weapon_type_combo.addItems(weapon_types)

    def on_weapon_type_changed(self, index):
        """Handle weapon type selection change"""
        if index < 0:
            return

        weapon_type = self.weapon_type_combo.currentText()
        self.clear_parts_ui()
        self.selected_parts = {}

        # Get part types for the selected weapon type
        part_types = self.api.get_part_types(weapon_type)
        for part_type in part_types:
            self.add_part_selection(weapon_type, part_type)

    def clear_parts_ui(self):
        """Clear the parts selection UI"""
        while self.parts_layout.count():
            item = self.parts_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def refresh_all_parts(self):
        """Refresh all part selections"""
        weapon_type = self.weapon_type_combo.currentText()
        if not weapon_type:
            return

        for i in range(self.parts_layout.count()):
            widget = self.parts_layout.itemAt(i).widget()
            if isinstance(widget, QtWidgets.QGroupBox):
                part_type = widget.title()
                self.refresh_parts(weapon_type, part_type)

    def refresh_parts(self, weapon_type=None, part_type=None):
        """Refresh parts for a specific weapon type and part type"""
        if weapon_type is None:
            weapon_type = self.weapon_type_combo.currentText()
        if not weapon_type:
            return

        if part_type is None:
            self.refresh_all_parts()
            return

        self.load_parts(weapon_type, part_type)

    def add_part_selection(self, weapon_type, part_type):
        """Add a part selection group to the UI"""
        group = QtWidgets.QGroupBox(part_type)
        layout = QtWidgets.QVBoxLayout()

        # Preview area
        preview_layout = QtWidgets.QHBoxLayout()
        self.preview_label = QtWidgets.QLabel()
        self.preview_label.setFixedSize(200, 200)
        self.preview_label.setAlignment(QtCore.Qt.AlignCenter)
        self.set_default_preview(self.preview_label)
        preview_layout.addWidget(self.preview_label)
        layout.addLayout(preview_layout)

        # Parts grid
        parts_grid = QtWidgets.QGridLayout()
        self.parts_grids[part_type] = parts_grid
        layout.addLayout(parts_grid)

        # Navigation buttons
        nav_layout = QtWidgets.QHBoxLayout()
        prev_button = QtWidgets.QPushButton("Previous")
        next_button = QtWidgets.QPushButton("Next")
        prev_button.clicked.connect(
            lambda: self.navigate_parts(weapon_type, part_type, "prev")
        )
        next_button.clicked.connect(
            lambda: self.navigate_parts(weapon_type, part_type, "next")
        )
        nav_layout.addWidget(prev_button)
        nav_layout.addWidget(next_button)
        layout.addLayout(nav_layout)

        group.setLayout(layout)
        self.parts_layout.addWidget(group)

        # Load initial parts
        self.load_parts(weapon_type, part_type)

    def set_default_preview(self, label):
        """Set the default preview image for a part type"""
        pixmap = QtGui.QPixmap(200, 200)
        pixmap.fill(QtGui.QColor(50, 50, 50))
        label.setPixmap(pixmap)

    def load_parts(self, weapon_type, part_type):
        """Load parts for a specific weapon type and part type"""
        self.current_page = 1
        self._fetch_parts(weapon_type, part_type, self.current_page)

    def _fetch_parts(self, weapon_type, part_type, page):
        """Fetch parts from the API"""
        parts = self.api.get_weapon_parts(weapon_type, part_type, page)
        if parts:
            self.update_parts_display(part_type, parts)

    def update_parts_display(self, part_type, parts_data):
        """Update the parts display grid"""
        grid = self.parts_grids.get(part_type)
        if not grid:
            return

        # Clear existing items
        while grid.count():
            item = grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Add new parts
        row = 0
        col = 0
        max_cols = 4

        for part in parts_data:
            part_widget = QtWidgets.QPushButton()
            part_widget.setFixedSize(100, 100)
            part_widget.setIconSize(QtCore.QSize(80, 80))

            # Load and set icon
            if "icon_url" in part:
                self._load_part_icon(part_widget, part["icon_url"])

            part_widget.clicked.connect(
                lambda checked, p=part: self.update_part_preview(part_type, p)
            )
            grid.addWidget(part_widget, row, col)

            col += 1
            if col >= max_cols:
                col = 0
                row += 1

    def update_part_preview(self, part_type, part):
        """Update the preview for a selected part"""
        group = None
        for i in range(self.parts_layout.count()):
            widget = self.parts_layout.itemAt(i).widget()
            if isinstance(widget, QtWidgets.QGroupBox) and widget.title() == part_type:
                group = widget
                break

        if not group:
            return

        preview_label = group.findChild(QtWidgets.QLabel)
        if not preview_label:
            return

        if "icon_url" in part:
            self._load_part_icon(preview_label, part["icon_url"])
        else:
            self.set_default_preview(preview_label)

        self.selected_parts[part_type] = part

    def handle_network_response(self, reply):
        """Handle network response for image loading"""
        if reply.error() == QNetworkReply.NoError:
            data = reply.readAll()
            pixmap = QtGui.QPixmap()
            pixmap.loadFromData(data)
            if not pixmap.isNull():
                sender = self.sender()
                if isinstance(sender, QtWidgets.QPushButton):
                    sender.setIcon(QtGui.QIcon(pixmap))
                elif isinstance(sender, QtWidgets.QLabel):
                    sender.setPixmap(
                        pixmap.scaled(
                            sender.size(),
                            QtCore.Qt.KeepAspectRatio,
                            QtCore.Qt.SmoothTransformation,
                        )
                    )

    def create_loading_indicator(self):
        """Create a loading indicator widget"""
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout()
        spinner = QtWidgets.QProgressBar()
        spinner.setRange(0, 0)  # Indeterminate progress
        layout.addWidget(spinner)
        widget.setLayout(layout)
        return widget

    def _create_colored_preview(self, pixmap, part_type, part):
        """Create a colored preview for a part"""
        if not pixmap:
            return None

        # Create a colored version of the preview
        colored = QtGui.QPixmap(pixmap.size())
        colored.fill(QtGui.QColor(50, 50, 50))

        painter = QtGui.QPainter(colored)
        painter.setCompositionMode(QtGui.QPainter.CompositionMode_SourceOver)
        painter.drawPixmap(0, 0, pixmap)
        painter.end()

        return colored

    def navigate_parts(self, weapon_type, part_type, direction):
        """Navigate through parts pages"""
        if direction == "prev" and self.current_page > 1:
            self.current_page -= 1
        elif direction == "next":
            self.current_page += 1

        self._fetch_parts(weapon_type, part_type, self.current_page)

    def reset_selection(self):
        """Reset all part selections"""
        self.selected_parts = {}
        for i in range(self.parts_layout.count()):
            widget = self.parts_layout.itemAt(i).widget()
            if isinstance(widget, QtWidgets.QGroupBox):
                preview_label = widget.findChild(QtWidgets.QLabel)
                if preview_label:
                    self.set_default_preview(preview_label)

    def generate_weapon(self):
        """Generate the weapon from selected parts"""
        if not self.selected_parts:
            QtWidgets.QMessageBox.warning(
                self,
                "No Parts Selected",
                "Please select at least one part before generating the weapon.",
            )
            return

        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.generate_button.setEnabled(False)

        # Prepare assembly data
        assembly_data = {
            "weapon_type": self.weapon_type_combo.currentText(),
            "parts": self.selected_parts,
        }

        # Start generation in a separate thread
        threading.Thread(target=self._create_weapon, args=(assembly_data,)).start()

    def _create_weapon(self, assembly_data):
        """Create the weapon in a separate thread"""
        try:
            result = self.api.create_assembly(assembly_data)
            if result:
                QtCore.QMetaObject.invokeMethod(
                    self,
                    "on_weapon_assembled",
                    QtCore.Qt.QueuedConnection,
                    QtCore.Q_ARG(object, result.get("model_files", [])),
                    QtCore.Q_ARG(object, assembly_data),
                )
                QtCore.QMetaObject.invokeMethod(
                    self,
                    "on_generation_finished",
                    QtCore.Qt.QueuedConnection,
                    QtCore.Q_ARG(bool, True),
                )
            else:
                QtCore.QMetaObject.invokeMethod(
                    self,
                    "on_generation_finished",
                    QtCore.Qt.QueuedConnection,
                    QtCore.Q_ARG(bool, False),
                    QtCore.Q_ARG(str, "Failed to create weapon assembly"),
                )
        except Exception as e:
            QtCore.QMetaObject.invokeMethod(
                self,
                "on_generation_finished",
                QtCore.Qt.QueuedConnection,
                QtCore.Q_ARG(bool, False),
                QtCore.Q_ARG(str, str(e)),
            )

    def on_generation_finished(self, success, message=""):
        """Handle weapon generation completion"""
        self.progress_bar.setVisible(False)
        self.generate_button.setEnabled(True)

        if not success:
            QtWidgets.QMessageBox.critical(
                self, "Generation Failed", f"Failed to generate weapon: {message}"
            )

    def on_weapon_assembled(self, model_files, assembly_data):
        """Handle successful weapon assembly"""
        if not model_files:
            return

        # Create a new geometry node for the weapon
        parent = hou.node(self.node_path) if self.node_path else hou.node("/obj")
        weapon_node = parent.createNode("geo", "weapon_assembly")

        # Import the model files
        for i, model_file in enumerate(model_files):
            file_node = weapon_node.createNode("file", f"part_{i}")
            file_node.parm("file").set(model_file)

        # Layout the nodes
        weapon_node.layoutChildren()

        # Set the viewport to the new node
        if self.node_path:
            hou.ui.paneTabOfType(hou.paneTabType.SceneViewer).setCurrentNode(
                weapon_node
            )


def show_weapon_generator(node_path=None):
    """Show the weapon generator UI"""
    dialog = QtWidgets.QDialog(hou.ui.mainQtWindow())
    dialog.setWindowTitle("Weapon Generator")
    dialog.setMinimumSize(800, 600)

    layout = QtWidgets.QVBoxLayout()
    widget = WeaponGeneratorWidget(dialog, node_path)
    layout.addWidget(widget)
    dialog.setLayout(layout)

    dialog.show()
