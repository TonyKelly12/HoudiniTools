"""
Weapon Generator UI for Houdini
-------------------------------
This module provides a UI for the Weapon Generator HDA, allowing users to
browse and select weapon parts from an online parts library.
"""

import hou
import os
import json
import requests
from PySide2 import QtCore, QtWidgets, QtGui
from PySide2.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply
import tempfile
import threading
import time

# -----------------------------------------------------------------------------
# API Communication Class
# -----------------------------------------------------------------------------


class WeaponAssemblyAPI:
    """Class to handle communication with the 3D Weapon Assembly API"""

    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        # Cache API responses to reduce network calls
        self.cache = {}
        self.cache_timeout = 300  # 5 minutes
        self.cache_timestamps = {}

    def _check_cache(self, cache_key):
        """Check if valid cache exists for the key"""
        if cache_key in self.cache and cache_key in self.cache_timestamps:
            cache_time = self.cache_timestamps[cache_key]
            if time.time() - cache_time < self.cache_timeout:
                return True
        return False

    def _update_cache(self, cache_key, data):
        """Update cache with new data"""
        self.cache[cache_key] = data
        self.cache_timestamps[cache_key] = time.time()

    def test_connection(self):
        """Test connection to the API"""
        try:
            response = requests.get(f"{self.base_url}/", timeout=5)
            return response.status_code == 200
        except Exception as e:
            print(f"API connection error: {str(e)}")
            return False

    def get_weapon_types(self):
        """Get list of available weapon types"""
        cache_key = "weapon_types"
        if self._check_cache(cache_key):
            return self.cache[cache_key]

        # For now, return the enum values from model_schema.py directly
        # In a real implementation, this would be a dedicated API endpoint
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
        self._update_cache(cache_key, weapon_types)
        return weapon_types

    def get_part_types(self, weapon_type):
        """Get list of available part types for a specific weapon type"""
        cache_key = f"part_types_{weapon_type}"
        if self._check_cache(cache_key):
            return self.cache[cache_key]

        # Get appropriate part types based on weapon type
        # In a real implementation, this would be a dedicated API endpoint
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

        result = part_types.get(weapon_type.lower(), common_parts)
        self._update_cache(cache_key, result)
        return result

    def get_weapon_parts(self, weapon_type, part_type, page=1, limit=10):
        """Get parts for a specific weapon type and part type with pagination"""
        cache_key = f"parts_{weapon_type}_{part_type}_{page}_{limit}"
        if self._check_cache(cache_key):
            return self.cache[cache_key]

        try:
            skip = (page - 1) * limit
            url = (
                f"{self.base_url}/models/weapon-parts"
                f"?weapon_type={weapon_type}"
                f"&part_type={part_type}"
                f"&skip={skip}"
                f"&limit={limit}"
            )
            print(f"Requesting URL: {url}")
            response = requests.get(url, headers=self.headers)

            if response.status_code == 200:
                try:
                    data = response.json()
                    # Handle both direct list responses and paginated responses
                    if isinstance(data, dict) and "models" in data:
                        parts = data["models"]
                        print(f"Retrieved {len(parts)} parts from paginated response")
                    elif isinstance(data, list):
                        parts = data
                        print(f"Retrieved {len(parts)} parts from list response")
                    else:
                        print(f"Unexpected response format: {type(data)}")
                        parts = []

                    self._update_cache(cache_key, parts)
                    return parts
                except ValueError as e:
                    print(f"JSON parsing error: {str(e)}")
                    print(f"Response text: {response.text[:200]}")
                    return []
            else:
                print(f"API Error ({response.status_code}): {response.text}")
                return []
        except Exception as e:
            print(f"Error getting weapon parts: {str(e)}")
            return []

    def download_model(self, model_id, target_path=None):
        """Download a model file by its ID"""
        try:
            url = f"{self.base_url}/models/{model_id}"
            response = requests.get(url, stream=True)

            if response.status_code == 200:
                if target_path is None:
                    # Create a temporary file if no path specified
                    fd, target_path = tempfile.mkstemp(suffix=".fbx")
                    os.close(fd)

                with open(target_path, "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)

                return target_path
            else:
                print(f"API Error ({response.status_code}): {response.text}")
                return None
        except Exception as e:
            print(f"Error downloading model: {str(e)}")
            return None

    # Add to WeaponAssemblyAPI class
    def upload_model(self, model_file_path, icon_file_path, metadata):
        """Upload a model file with metadata to the API"""
        try:
            url = f"{self.base_url}/models/"

            # Prepare files
            files = {
                "file": (
                    os.path.basename(model_file_path),
                    open(model_file_path, "rb"),
                    "application/octet-stream",
                ),
                "icon": (
                    os.path.basename(icon_file_path),
                    open(icon_file_path, "rb"),
                    "image/png",
                ),
                "metadata_json": (None, json.dumps(metadata)),
            }

            # Make the request
            response = requests.post(url, files=files)

            if response.status_code == 200:
                return response.json()
            else:
                print(f"API Error ({response.status_code}): {response.text}")
                return None
        except Exception as e:
            print(f"Error uploading model: {str(e)}")
            return None

    def get_model_metadata(self, model_id):
        """Get metadata for a specific model"""
        cache_key = f"metadata_{model_id}"
        if self._check_cache(cache_key):
            return self.cache[cache_key]

        try:
            url = f"{self.base_url}/models/metadata/{model_id}"
            response = requests.get(url, headers=self.headers)

            if response.status_code == 200:
                data = response.json()
                self._update_cache(cache_key, data)
                return data
            else:
                print(f"API Error ({response.status_code}): {response.text}")
                return None
        except Exception as e:
            print(f"Error getting model metadata: {str(e)}")
            return None

    def create_assembly(self, assembly_data):
        """Create a new weapon assembly"""
        try:
            url = f"{self.base_url}/assemblies"
            response = requests.post(url, json=assembly_data, headers=self.headers)

            if response.status_code == 200:
                return response.json()
            else:
                print(f"API Error ({response.status_code}): {response.text}")
                return None
        except Exception as e:
            print(f"Error creating assembly: {str(e)}")
            return None


# -----------------------------------------------------------------------------
# Weapon Generator UI Class
# -----------------------------------------------------------------------------


class WeaponGeneratorWidget(QtWidgets.QWidget):
    """Widget for the Weapon Generator UI"""

    # Signal definitions
    connectionStatusChanged = QtCore.Signal(bool)
    partsLoaded = QtCore.Signal(str, object)
    generationFinished = QtCore.Signal(bool, str)
    weaponAssembled = QtCore.Signal(object, object)
    progressUpdated = QtCore.Signal(int)

    def __init__(self, parent=None, node_path=None):
        super(WeaponGeneratorWidget, self).__init__(parent)

        # Store node path for later use
        self.node_path = node_path

        # Initialize API client
        self.api = WeaponAssemblyAPI()

        # Storage for currently selected parts
        self.selected_parts = {}
        self.part_widgets = {}
        self.current_pages = {}
        self.has_more_pages = {}

        # Part previews and models dictionary
        self.part_models = {}

        # Create UI
        self.create_ui()

        # Connect signals to slots
        self.connectionStatusChanged.connect(self.update_connection_status)
        self.partsLoaded.connect(self.update_parts_display)
        self.generationFinished.connect(self.on_generation_finished)
        self.weaponAssembled.connect(self.on_weapon_assembled)
        self.progressUpdated.connect(self.update_progress)
        # Test API connection and initialize
        self.initialize()

    def update_progress(self, value):
        """Update the progress dialog - triggered from signal"""
        if hasattr(self, "progress_dialog") and self.progress_dialog:
            self.progress_dialog.setValue(value)

    def create_ui(self):
        """Create the user interface"""
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # Status bar for connection status
        self.status_layout = QtWidgets.QHBoxLayout()
        self.status_label = QtWidgets.QLabel("Connecting to API...")
        self.status_indicator = QtWidgets.QLabel()
        self.status_indicator.setFixedSize(16, 16)
        self.status_indicator.setStyleSheet(
            "background-color: yellow; border-radius: 8px;"
        )

        self.status_layout.addWidget(self.status_indicator)
        self.status_layout.addWidget(self.status_label)
        self.status_layout.addStretch()

        # API URL configuration
        self.url_layout = QtWidgets.QHBoxLayout()
        self.url_label = QtWidgets.QLabel("API URL:")
        self.url_input = QtWidgets.QLineEdit("http://localhost:8000")
        self.url_input.setPlaceholderText("http://localhost:8000")
        self.connect_button = QtWidgets.QPushButton("Connect")
        self.connect_button.clicked.connect(self.test_connection)

        self.url_layout.addWidget(self.url_label)
        self.url_layout.addWidget(self.url_input, 1)
        self.url_layout.addWidget(self.connect_button)

        # Weapon type selection
        self.type_layout = QtWidgets.QHBoxLayout()
        self.type_label = QtWidgets.QLabel("Weapon Type:")
        self.type_combo = QtWidgets.QComboBox()
        self.type_combo.setMinimumWidth(150)
        self.type_combo.currentIndexChanged.connect(self.on_weapon_type_changed)

        self.type_layout.addWidget(self.type_label)
        self.type_layout.addWidget(self.type_combo)
        self.type_layout.addStretch()

        # Parts selection area will be added dynamically
        self.parts_layout = QtWidgets.QHBoxLayout()
        self.parts_layout.setSpacing(15)

        # Scroll area for parts
        self.scroll_area = QtWidgets.QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.scroll_area.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)

        self.scroll_widget = QtWidgets.QWidget()
        self.scroll_widget.setLayout(self.parts_layout)
        self.scroll_area.setWidget(self.scroll_widget)

        # Action buttons
        self.action_layout = QtWidgets.QHBoxLayout()
        self.create_button = QtWidgets.QPushButton("Generate Weapon")
        self.create_button.setMinimumHeight(40)
        self.create_button.clicked.connect(self.generate_weapon)

        self.reset_button = QtWidgets.QPushButton("Reset")
        self.reset_button.clicked.connect(self.reset_selection)

        self.action_layout.addWidget(self.reset_button)
        self.action_layout.addStretch()
        self.action_layout.addWidget(self.create_button)

        # Add all layouts to main layout
        main_layout.addLayout(self.status_layout)
        main_layout.addLayout(self.url_layout)
        main_layout.addLayout(self.type_layout)
        main_layout.addWidget(self.scroll_area)
        main_layout.addLayout(self.action_layout)

    def initialize(self):
        """Initialize the widget with API data"""
        self.test_connection()

    def test_connection(self):
        """Test connection to the API"""
        # Update API URL from input field
        self.api.base_url = self.url_input.text().strip()

        # Disable UI during connection test
        self.setEnabled(False)
        self.status_indicator.setStyleSheet(
            "background-color: yellow; border-radius: 8px;"
        )
        self.status_label.setText("Testing connection...")

        # Run connection test in a separate thread to avoid UI freezing
        threading.Thread(target=self._run_test).start()

    def _run_test(self):
        """Run the connection test in a background thread"""
        try:
            connected = self.api.test_connection()

            # Use a signal to update UI from the main thread
            self.connectionStatusChanged.emit(connected)
        except Exception as e:
            print(f"Connection test error: {str(e)}")
            self.connectionStatusChanged.emit(False)

    def update_connection_status(self, connected):
        """Update UI based on connection status - triggered from signal"""
        self.setEnabled(True)

        if connected:
            self.status_indicator.setStyleSheet(
                "background-color: green; border-radius: 8px;"
            )
            self.status_label.setText("Connected to API")

            # Load weapon types
            self.load_weapon_types()
        else:
            self.status_indicator.setStyleSheet(
                "background-color: red; border-radius: 8px;"
            )
            self.status_label.setText("Failed to connect to API")

    def load_weapon_types(self):
        """Load weapon types from API"""
        weapon_types = self.api.get_weapon_types()

        # Clear and populate combo box
        self.type_combo.clear()

        for weapon_type in weapon_types:
            # Capitalize the first letter for display
            display_name = weapon_type.capitalize()
            self.type_combo.addItem(display_name, weapon_type)

    def on_weapon_type_changed(self, index):
        """Handle weapon type selection change"""
        if index < 0:
            return

        # Clear previous parts UI
        self.clear_parts_ui()

        # Reset selection
        self.selected_parts = {}
        self.part_models = {}

        # Get weapon type
        weapon_type = self.type_combo.itemData(index)

        # Get part types for the selected weapon type
        part_types = self.api.get_part_types(weapon_type)

        # Create UI for each part type
        for part_type in part_types:
            self.add_part_selection(weapon_type, part_type)

    def clear_parts_ui(self):
        """Clear the parts UI layout"""
        # Remove all widgets from the layout
        while self.parts_layout.count():
            item = self.parts_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Clear tracking dictionaries
        self.part_widgets = {}
        self.current_pages = {}
        self.has_more_pages = {}

    def add_part_selection(self, weapon_type, part_type):
        """Add UI elements for selecting a part type"""
        # Create a container widget for this part type
        part_widget = QtWidgets.QWidget()
        part_layout = QtWidgets.QVBoxLayout(part_widget)
        part_layout.setContentsMargins(0, 0, 0, 0)

        # Part type label
        part_label = QtWidgets.QLabel(part_type.capitalize())
        part_label.setAlignment(QtCore.Qt.AlignCenter)
        part_label.setStyleSheet("font-weight: bold; font-size: 14px;")

        # Part selection area
        selection_widget = QtWidgets.QWidget()
        selection_layout = QtWidgets.QVBoxLayout(selection_widget)
        selection_layout.setContentsMargins(0, 0, 0, 0)

        # Preview area
        preview_frame = QtWidgets.QFrame()
        preview_frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        preview_frame.setMinimumSize(130, 130)
        preview_frame.setMaximumSize(130, 130)

        # Preview image
        preview_label = QtWidgets.QLabel()
        preview_label.setAlignment(QtCore.Qt.AlignCenter)
        preview_label.setStyleSheet("background-color: #333333;")
        preview_label.setMinimumSize(120, 120)
        preview_label.setMaximumSize(120, 120)

        # Default preview
        self.set_default_preview(preview_label)

        preview_layout = QtWidgets.QVBoxLayout(preview_frame)
        preview_layout.setContentsMargins(5, 5, 5, 5)
        preview_layout.addWidget(preview_label)

        # Navigation buttons
        nav_layout = QtWidgets.QHBoxLayout()

        prev_btn = QtWidgets.QPushButton("↑")
        prev_btn.setFixedWidth(40)
        prev_btn.clicked.connect(
            lambda: self.navigate_parts(weapon_type, part_type, -1)
        )

        next_btn = QtWidgets.QPushButton("↓")
        next_btn.setFixedWidth(40)
        next_btn.clicked.connect(lambda: self.navigate_parts(weapon_type, part_type, 1))

        nav_layout.addWidget(prev_btn)
        nav_layout.addWidget(next_btn)

        # Info label
        info_label = QtWidgets.QLabel("Loading...")
        info_label.setAlignment(QtCore.Qt.AlignCenter)
        info_label.setWordWrap(True)
        info_label.setMinimumHeight(40)

        # Add all elements to the part layout
        part_layout.addWidget(part_label)
        part_layout.addWidget(preview_frame, 0, QtCore.Qt.AlignCenter)
        part_layout.addLayout(nav_layout)
        part_layout.addWidget(info_label)

        # Store widgets for later access
        self.part_widgets[part_type] = {
            "widget": part_widget,
            "preview": preview_label,
            "info": info_label,
            "prev_btn": prev_btn,
            "next_btn": next_btn,
        }

        # Add to the main parts layout
        self.parts_layout.addWidget(part_widget)

        # Initialize parts page
        self.current_pages[part_type] = 1
        self.has_more_pages[part_type] = True

        # Load initial parts
        self.load_parts(weapon_type, part_type)

    def set_default_preview(self, label):
        """Set a default preview image"""
        # Create a simple icon with the part type
        pixmap = QtGui.QPixmap(120, 120)
        pixmap.fill(QtCore.Qt.transparent)

        painter = QtGui.QPainter(pixmap)
        painter.setPen(QtGui.QPen(QtGui.QColor("#888888")))
        painter.setFont(QtGui.QFont("Arial", 12))
        painter.drawText(pixmap.rect(), QtCore.Qt.AlignCenter, "No\nPreview")
        painter.end()

        label.setPixmap(pixmap)

    def load_parts(self, weapon_type, part_type):
        """Load parts for a specific weapon type and part type"""
        # Get current page
        page = self.current_pages.get(part_type, 1)

        # Update UI to show loading
        if part_type in self.part_widgets:
            widgets = self.part_widgets[part_type]
            widgets["info"].setText("Loading...")

        # Load parts in a background thread
        threading.Thread(
            target=self._fetch_parts, args=(weapon_type, part_type, page)
        ).start()

    def _fetch_parts(self, weapon_type, part_type, page):
        """Fetch parts in a background thread with better error handling and debugging"""
        try:
            print(f"Fetching {weapon_type} {part_type} parts (page {page})...")
            parts = self.api.get_weapon_parts(weapon_type, part_type, page=page)

            if isinstance(parts, dict) and "models" in parts:
                # Handle the case where the API returns a dictionary with "models" key
                parts_data = parts["models"]
            elif isinstance(parts, list):
                # Handle the case where the API returns a list directly
                parts_data = parts
            else:
                print(f"Warning: Unexpected parts data format: {type(parts)}")
                parts_data = []

            print(f"Received {len(parts_data)} parts for {part_type}")

            # Use signal to update UI from main thread
            self.partsLoaded.emit(part_type, parts_data)
        except Exception as e:
            print(f"Error fetching parts: {str(e)}")
            self.partsLoaded.emit(part_type, [])

    def update_parts_display(self, part_type, parts_data):
        """Update the parts display with loaded data - triggered from signal"""
        if part_type not in self.part_widgets:
            return

        widgets = self.part_widgets[part_type]

        # Debug print
        print(f"Updating display for {part_type} with {len(parts_data)} parts")

        # Check if we have parts
        if parts_data and len(parts_data) > 0:
            # Store all parts for this type
            self.part_models[part_type] = parts_data

            # If we don't already have a selection for this part type, select the first part
            if part_type not in self.selected_parts or not self.selected_parts[part_type]:
                part = parts_data[0]
                self.selected_parts[part_type] = part.get("id")

                # Display part info
                name = part.get("metadata", {}).get("name", "Unknown")
                widgets["info"].setText(name)

                # Update preview (if available)
                self.update_part_preview(part_type, part)
            else:
                # We already have a selection, find that part and display it
                part_id = self.selected_parts[part_type]
                found = False

                for part in parts_data:
                    if part.get("id") == part_id:
                        # Display part info
                        name = part.get("metadata", {}).get("name", "Unknown")
                        widgets["info"].setText(name)

                        # Update preview
                        self.update_part_preview(part_type, part)
                        found = True
                        break
                    
                # If we couldn't find the selected part in the new data, reset to the first one
                if not found and parts_data:
                    part = parts_data[0]
                    self.selected_parts[part_type] = part.get("id")

                    # Display part info
                    name = part.get("metadata", {}).get("name", "Unknown")
                    widgets["info"].setText(name)

                    # Update preview
                    self.update_part_preview(part_type, part)

            # Enable/disable navigation buttons
            widgets["prev_btn"].setEnabled(self.current_pages[part_type] > 1 or len(parts_data) > 1)
            widgets["next_btn"].setEnabled(self.has_more_pages[part_type] or len(parts_data) > 1)

            # Update pagination status
            self.has_more_pages[part_type] = len(parts_data) >= 10  # Assuming page size of 10
        else:
            # No parts found
            widgets["info"].setText("No parts found")
            widgets["prev_btn"].setEnabled(False)
            widgets["next_btn"].setEnabled(False)
            self.set_default_preview(widgets["preview"])

            # Clear parts for this type
            self.part_models[part_type] = []

            if part_type in self.selected_parts:
                del self.selected_parts[part_type]

    def update_part_preview(self, part_type, part):
        """Update the preview for a part with improved image handling"""
        if part_type not in self.part_widgets:
            return

        part_id = part.get("id")
        preview_label = self.part_widgets[part_type]["preview"]

        # Create a placeholder pixmap
        placeholder = QtGui.QPixmap(120, 120)
        placeholder.fill(QtCore.Qt.transparent)

        # Try to download the icon from the API
        try:
            icon_url = f"{self.api.base_url}/models/icons/{part_id}"

            # Use QNetworkAccessManager for more reliable image loading
            if not hasattr(self, 'network_manager'):
                self.network_manager = QtNetwork.QNetworkAccessManager()
                self.network_manager.finished.connect(self.handle_network_response)

            # Store the request context
            request = QtNetwork.QNetworkRequest(QtCore.QUrl(icon_url))
            request.setAttribute(QtNetwork.QNetworkRequest.User, part_type)
            self.network_manager.get(request)

            # Show loading indicator while waiting for image
            spinner_pixmap = self.create_loading_indicator()
            preview_label.setPixmap(spinner_pixmap)

        except Exception as e:
            print(f"Error initiating icon download: {str(e)}")
            self._create_colored_preview(placeholder, part_type, part)
            preview_label.setPixmap(placeholder)

    def handle_network_response(self, reply):
        """Handle the network response for image downloads"""
        part_type = reply.request().attribute(QtNetwork.QNetworkRequest.User)

        if part_type not in self.part_widgets:
            return

        preview_label = self.part_widgets[part_type]["preview"]

        # Get error if any
        error = reply.error()

        if error == QtNetwork.QNetworkReply.NoError:
            try:
                # Read the image data
                image_data = reply.readAll()

                # Create QImage first to validate and handle both PNG and JPEG
                image = QtGui.QImage()
                if image.loadFromData(image_data):
                    # Convert to pixmap if valid
                    pixmap = QtGui.QPixmap.fromImage(image)
                    # Scale to fit
                    pixmap = pixmap.scaled(
                        120, 120, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation
                    )
                    preview_label.setPixmap(pixmap)
                else:
                    # Invalid image data
                    raise Exception("Invalid image data")

            except Exception as e:
                print(f"Error processing image data: {str(e)}")
                # Fall back to colored preview if we have a part in our data
                for part_type_key, parts in self.part_models.items():
                    if part_type_key == part_type:
                        for part in parts:
                            if part.get("id") == reply.url().toString().split('/')[-1]:
                                placeholder = QtGui.QPixmap(120, 120)
                                placeholder.fill(QtCore.Qt.transparent)
                                self._create_colored_preview(placeholder, part_type, part)
                                preview_label.setPixmap(placeholder)
                                return

                # Default fallback
                self.set_default_preview(preview_label)
        else:
            print(f"Network error: {reply.errorString()}")
            self.set_default_preview(preview_label)

    def create_loading_indicator(self):
        """Create a loading spinner indicator"""
        pixmap = QtGui.QPixmap(120, 120)
        pixmap.fill(QtCore.Qt.transparent)

        painter = QtGui.QPainter(pixmap)
        painter.setPen(QtGui.QPen(QtGui.QColor("#888888")))
        painter.setBrush(QtGui.QBrush(QtCore.Qt.NoBrush))
        painter.drawEllipse(40, 40, 40, 40)
        painter.setFont(QtGui.QFont("Arial", 10))
        painter.drawText(pixmap.rect(), QtCore.Qt.AlignCenter, "Loading...")
        painter.end()

        return pixmap    

    def _create_colored_preview(self, pixmap, part_type, part):
        """Create a colored preview with text as fallback"""
        # Your existing preview generation code
        colors = {
            "handle": "#8B4513",  # Brown
            # ... other colors ...
        }
        color = colors.get(part_type, "#888888")
        pixmap.fill(QtGui.QColor(color))

        # Add the part name
        painter = QtGui.QPainter(pixmap)
        painter.setPen(QtGui.QPen(QtCore.Qt.white))
        painter.setFont(QtGui.QFont("Arial", 10))

        name = part.get("metadata", {}).get("name", "Unknown")
        # Truncate long names
        if len(name) > 20:
            name = name[:17] + "..."

        painter.drawText(pixmap.rect(), QtCore.Qt.AlignCenter, name)
        painter.end()

    def navigate_parts(self, weapon_type, part_type, direction):
        """Navigate through parts (previous/next) with improved cycling"""
        if part_type not in self.part_models:
            return

        parts = self.part_models.get(part_type, [])
        if not parts:
            return  # No parts to navigate through

        # Debug print to see what we're working with
        print(f"Navigate {part_type}: {len(parts)} parts available, direction: {direction}")

        # Find current selected index
        current_id = self.selected_parts.get(part_type)
        current_index = -1

        for i, part in enumerate(parts):
            if part.get("id") == current_id:
                current_index = i
                break

        # If we couldn't find the current part, reset to the first one
        if current_index < 0 and parts:
            current_index = 0

        # Calculate new index with proper wrapping
        if direction < 0:  # UP button (previous)
            if current_index <= 0:
                # We need to load the previous page if it exists
                if self.current_pages[part_type] > 1:
                    self.current_pages[part_type] -= 1
                    print(f"Loading previous page for {part_type}: page {self.current_pages[part_type]}")
                    self.load_parts(weapon_type, part_type)
                    return
                else:
                    # Wrap around to the last item if we're at the first page
                    new_index = len(parts) - 1
            else:
                new_index = current_index - 1
        else:  # DOWN button (next)
            if current_index >= len(parts) - 1:
                # We need to load the next page if it exists
                if self.has_more_pages[part_type]:
                    self.current_pages[part_type] += 1
                    print(f"Loading next page for {part_type}: page {self.current_pages[part_type]}")
                    self.load_parts(weapon_type, part_type)
                    return
                else:
                    # Wrap around to the first item if we're at the last page
                    new_index = 0
            else:
                new_index = current_index + 1

        print(f"Navigating from index {current_index} to {new_index}")

        # Update selection to the new index
        if 0 <= new_index < len(parts):
            new_part = parts[new_index]
            self.selected_parts[part_type] = new_part.get("id")

            # Update display
            if part_type in self.part_widgets:
                widgets = self.part_widgets[part_type]
                name = new_part.get("metadata", {}).get("name", "Unknown")
                widgets["info"].setText(name)
                self.update_part_preview(part_type, new_part)
        else:
            print(f"Warning: Invalid new index {new_index} for {part_type}")

    def reset_selection(self):
        """Reset part selection"""
        # Get current weapon type
        index = self.type_combo.currentIndex()
        if index >= 0:
            # Re-trigger weapon type changed to reset everything
            self.on_weapon_type_changed(index)

    def generate_weapon(self):
        """Generate the assembled weapon"""
        # Check if we have all required parts
        if not self.selected_parts:
            QtWidgets.QMessageBox.warning(
                self, "Missing Parts", "Please select parts for your weapon first."
            )
            return

        # Get weapon type
        weapon_type_index = self.type_combo.currentIndex()
        if weapon_type_index < 0:
            return

        weapon_type = self.type_combo.itemData(weapon_type_index)

        # Create assembly data
        assembly_parts = []
        for part_type, part_id in self.selected_parts.items():
            # Basic positioning - in a real implementation, this would be more sophisticated
            # with proper offsets based on weapon type and part types
            position = {"x": 0, "y": 0, "z": 0}

            # Simple vertical stacking for now
            if part_type == "blade":
                position["y"] = 1.0
            elif part_type == "guard":
                position["y"] = 0.5
            elif part_type == "pommel":
                position["y"] = -0.5
            elif part_type == "head":
                position["y"] = 1.0

            assembly_parts.append(
                {
                    "model_id": part_id,
                    "part_type": part_type,
                    "position": position,
                    "rotation": {"x": 0, "y": 0, "z": 0},
                    "scale": {"x": 1, "y": 1, "z": 1},
                }
            )

        assembly_data = {
            "name": f"Generated {weapon_type.capitalize()}",
            "description": "Generated using Weapon Generator HDA",
            "weapon_type": weapon_type,
            "parts": assembly_parts,
            "created_at": None,  # Will be set by API
            "updated_at": None,  # Will be set by API
            "tags": ["hda_generated"],
        }

        # Disable UI during process
        self.setEnabled(False)
        self.status_label.setText("Generating weapon...")

        # Show progress dialog
        self.progress = QtWidgets.QProgressDialog(
            "Generating weapon...", "Cancel", 0, 100, self
        )
        self.progress.setWindowModality(QtCore.Qt.WindowModal)
        self.progress.setMinimumDuration(0)
        self.progress.setValue(10)

        # Download and assemble parts in a separate thread
        threading.Thread(target=self._create_weapon, args=(assembly_data,)).start()

    def _create_weapon(self, assembly_data):
        """Create a weapon in a background thread"""
        try:
            # We'd use API to create the assembly but for now we'll download the models
            # assembly_result = self.api.create_assembly(assembly_data)

            # Update progress to 20%
            self.progressUpdated.emit(20)

            # Download all selected parts
            model_files = {}
            i = 0
            total_parts = len(self.selected_parts)

            for part_type, part_id in self.selected_parts.items():
                # Skip if cancelled
                if (
                    hasattr(self, "progress_dialog")
                    and self.progress_dialog.wasCanceled()
                ):
                    self.generationFinished.emit(False, "Cancelled by user")
                    return

                # Download the model
                model_path = self.api.download_model(part_id)
                if model_path:
                    model_files[part_type] = model_path

                # Update progress
                i += 1
                progress_value = 20 + int(60 * (i / total_parts))
                self.progressUpdated.emit(progress_value)

            # Process is complete, update progress
            self.progressUpdated.emit(90)

            # Signal to assemble parts in the main thread
            self.weaponAssembled.emit(model_files, assembly_data)

        except Exception as e:
            print(f"Error creating weapon: {str(e)}")
            self.generationFinished.emit(False, str(e))

    def on_generation_finished(self, success, message=""):
        """Handle weapon generation completion - triggered from signal"""
        # Re-enable UI
        self.setEnabled(True)

        if success:
            self.status_label.setText("Weapon generated successfully")
        else:
            self.status_label.setText(f"Generation failed: {message}")
            QtWidgets.QMessageBox.warning(
                self, "Generation Failed", f"Failed to generate weapon: {message}"
            )

    def on_weapon_assembled(self, model_files, assembly_data):
        """Assemble downloaded weapon parts in Houdini - triggered from signal"""
        try:
            # Get the node
            node = None
            if self.node_path:
                node = hou.node(self.node_path)

            if not node:
                # Try to get parent node in /obj context
                node = hou.node("/obj")

            # Print node path and type for debugging
            print(f"Parent node: {node.path()}, Type: {node.type().name()}")

            # Create a new null node to hold our output
            # Use fully qualified node type names
            weapon_node = node.createNode("null", "OUTPUT_Weapon")
            print(f"Created weapon node: {weapon_node.path()}")

            # Create merge node to combine parts
            merge_node = node.createNode("merge", "MERGE_Parts")
            print(f"Created merge node: {merge_node.path()}")

            # Connect merge to weapon
            weapon_node.setInput(0, merge_node)

            # Add each part
            input_index = 0

            # First make sure the output directory exists
            out_dir = os.path.join(os.path.dirname(node.path()), "weapon_parts")
            try:
                os.makedirs(out_dir)
            except OSError:
                pass

            for part_type, model_path in model_files.items():
                # Find part data in assembly
                part_data = None
                for part in assembly_data.get("parts", []):
                    if part.get("part_type") == part_type:
                        part_data = part
                        break

                if not part_data:
                    continue

                # Get position, rotation, scale
                position = part_data.get("position", {"x": 0, "y": 0, "z": 0})
                rotation = part_data.get("rotation", {"x": 0, "y": 0, "z": 0})
                scale = part_data.get("scale", {"x": 1, "y": 1, "z": 1})

                try:
                    # Import model file - create a geo node instead
                    geo_node = node.createNode("geo", f"GEO_{part_type}")
                    print(f"Created geo node: {geo_node.path()}")

                    # Inside the geo node, create a file node to import the model
                    file_node = geo_node.createNode("file", f"FILE_{part_type}")
                    print(f"Created file node: {file_node.path()}")

                    # Set file path
                    file_node.parm("file").set(model_path)

                    # Create transform node for positioning
                    # Use geo node's transform parameters
                    geo_node.parmTuple("t").set(
                        [
                            position.get("x", 0),
                            position.get("y", 0),
                            position.get("z", 0),
                        ]
                    )
                    geo_node.parmTuple("r").set(
                        [
                            rotation.get("x", 0),
                            rotation.get("y", 0),
                            rotation.get("z", 0),
                        ]
                    )
                    geo_node.parmTuple("s").set(
                        [scale.get("x", 1), scale.get("y", 1), scale.get("z", 1)]
                    )

                    # Connect to merge node
                    merge_node.setInput(input_index, geo_node)
                    input_index += 1
                except Exception as e:
                    print(f"Error creating nodes for {part_type}: {str(e)}")

            # Cook the nodes
            weapon_node.cook(force=True)

            # Signal completion
            self.generationFinished.emit(True, "")

            # Select the output node
            weapon_node.setSelected(True)

        except Exception as e:
            print(f"Error in on_weapon_assembled: {str(e)}")
            import traceback

            traceback.print_exc()
            self.generationFinished.emit(False, str(e))


# -----------------------------------------------------------------------------
# Module Interface Functions
# -----------------------------------------------------------------------------


def show_weapon_generator(node_path=None):
    """Show the Weapon Generator UI"""
    # Create a dialog to hold our widget
    dialog = QtWidgets.QDialog(hou.qt.mainWindow())
    dialog.setWindowTitle("Weapon Generator")
    dialog.setMinimumSize(800, 600)

    # Create layout
    layout = QtWidgets.QVBoxLayout(dialog)

    # Create tab widget
    tab_widget = QtWidgets.QTabWidget()

    # Create our widgets
    generator_widget = WeaponGeneratorWidget(dialog, node_path)
    upload_widget = WeaponPartUploadWidget(dialog, generator_widget.api)

    # Add tabs
    tab_widget.addTab(generator_widget, "Generate Weapon")
    tab_widget.addTab(upload_widget, "Upload Parts")

    layout.addWidget(tab_widget)

    # Show the dialog
    dialog.exec_()

    return dialog


# -----------------------------------------------------------------------------
# Module Upload Widget
# -----------------------------------------------------------------------------


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
            QtWidgets.QMessageBox.warning(self, "Missing Information", "Please enter a name for the part.")
            return

        if not self.model_path_label.text():
            QtWidgets.QMessageBox.warning(self, "Missing File", "Please select a model file to upload.")
            return

        if not self.icon_path_label.text():
            QtWidgets.QMessageBox.warning(self, "Missing File", "Please select an icon/preview image.")
            return

        # Prepare metadata
        tags = [tag.strip() for tag in self.tags_input.text().split(",") if tag.strip()]

        material_slots = None
        if self.material_slots_input.text().strip():
            material_slots = [slot.strip() for slot in self.material_slots_input.text().split(",") if slot.strip()]

        # Prepare weapon part metadata
        weapon_part_metadata = None
        if self.is_weapon_part.isChecked():
            weapon_part_metadata = {
                "weapon_type": self.weapon_type_combo.currentData(),
                "part_type": self.part_type_combo.currentData(),
                "is_attachment": False,
                "material_slots": material_slots
            }

            # Add variant info if provided
            if self.variant_name_input.text().strip():
                weapon_part_metadata["variant_name"] = self.variant_name_input.text().strip()

            if self.variant_group_input.text().strip():
                weapon_part_metadata["variant_group"] = self.variant_group_input.text().strip()

        # Prepare metadata JSON
        metadata = {
            "name": self.name_input.text().strip(),
            "description": self.description_input.toPlainText().strip(),
            "format": os.path.splitext(self.model_path_label.text())[1][1:].lower(),
            "category": self.category_input.text().strip() or "weapons",
            "is_weapon_part": self.is_weapon_part.isChecked()
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
                self.progress_dialog
            )
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
        if hasattr(self, 'progress_dialog') and self.progress_dialog:
            self.progress_dialog.close()

        if success:
            # Show success message
            QtWidgets.QMessageBox.information(self, "Upload Complete", message)

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
                with open(model_path, 'rb') as test_model:
                    model_size = os.path.getsize(model_path)
                    print(f"Model file opened successfully. Size: {model_size} bytes")
                    
                with open(icon_path, 'rb') as test_icon:
                    icon_size = os.path.getsize(icon_path)
                    print(f"Icon file opened successfully. Size: {icon_size} bytes")
            except Exception as file_error:
                print(f"File access error: {str(file_error)}")
                self.uploadCompleted.emit(False, f"File access error: {str(file_error)}")
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
            if self.api and hasattr(self.api, 'base_url'):
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
                model_file = open(model_path, 'rb')
                icon_file = open(icon_path, 'rb')
                
                files = {
                    'file': (os.path.basename(model_path), model_file, 'application/octet-stream'),
                    'icon': (os.path.basename(icon_path), icon_file, 'image/png')
                }
                
                data = {
                    'metadata_json': metadata_json
                }
                
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
                            self.uploadCompleted.emit(True, f"Part ID: {result.get('id', 'unknown')}")
                        except Exception as json_error:
                            print(f"Error parsing response JSON: {str(json_error)}")
                            print(f"Response text: {response.text[:500]}")
                            self.uploadCompleted.emit(False, f"Error parsing response: {str(json_error)}")
                    else:
                        print(f"Error response: {response.status_code} - {response.text[:500]}")
                        self.uploadCompleted.emit(False, f"Upload failed with status {response.status_code}: {response.text[:200]}")
                except requests.exceptions.Timeout:
                    print("Request timed out after 120 seconds")
                    self.uploadCompleted.emit(False, "Request timed out (2 minutes)")
                except requests.exceptions.ConnectionError as conn_error:
                    print(f"Connection error: {str(conn_error)}")
                    self.uploadCompleted.emit(False, f"Connection error: {str(conn_error)}")
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
                self.uploadCompleted.emit(False, f"Error opening files: {str(file_open_error)}")
                
        except Exception as e:
            import traceback
            print("Exception in upload process:")
            traceback.print_exc()
            self.uploadCompleted.emit(False, f"Upload error: {str(e)}")
        finally:
            # Ensure progress is completed in all cases
            self.progressUpdated.emit(100)
            print("Upload process completed")

    def on_upload_completed(self, success, message):
        """Handle upload completion - triggered from signal"""
        # Re-enable UI
        self.setEnabled(True)

        if success:
            # Show success message
            QtWidgets.QMessageBox.information(self, "Upload Complete", message)

            # Clear form for next upload
            self.clear_form()
        else:
            # Show error message
            QtWidgets.QMessageBox.warning(self, "Upload Failed", message)

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
