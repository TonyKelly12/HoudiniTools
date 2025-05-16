"""
Weapon Generator HDA Python Module
----------------------------------
This module handles all backend logic for the Weapon Generator HDA, including:
- API communication with the 3D Weapon Assembly API
- UI creation and management
- Part visualization and selection
- Weapon assembly and output generation
"""

import hou
import os
import sys
import json
import requests
from PySide2 import QtCore, QtWidgets, QtGui
import tempfile
import subprocess
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
            "Accept": "application/json"
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
            return False

    def get_weapon_types(self):
        """Get list of available weapon types"""
        cache_key = "weapon_types"
        if self._check_cache(cache_key):
            return self.cache[cache_key]
            
        # For now, return the enum values from model_schema.py directly
        # In a real implementation, this would be a dedicated API endpoint
        weapon_types = [
            "sword", "axe", "mace", "bow", "spear", 
            "dagger", "staff", "shield", "gun", "rifle", "custom"
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
            "custom": ["handle", "body", "custom"]
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
            url = f"{self.base_url}/models/weapon-parts?weapon_type={weapon_type}&part_type={part_type}&skip={skip}&limit={limit}"
            response = requests.get(url, headers=self.headers)
            
            if response.status_code == 200:
                data = response.json()
                self._update_cache(cache_key, data)
                return data
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
                
                with open(target_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                return target_path
            else:
                print(f"API Error ({response.status_code}): {response.text}")
                return None
        except Exception as e:
            print(f"Error downloading model: {str(e)}")
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
    
    def __init__(self, parent=None):
        super(WeaponGeneratorWidget, self).__init__(parent)
        
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
        
        # Test API connection and initialize
        self.initialize()
    
    def create_ui(self):
        """Create the user interface"""
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # Status bar for connection status
        self.status_layout = QtWidgets.QHBoxLayout()
        self.status_label = QtWidgets.QLabel("Connecting to API...")
        self.status_indicator = QtWidgets.QLabel()
        self.status_indicator.setFixedSize(16, 16)
        self.status_indicator.setStyleSheet("background-color: yellow; border-radius: 8px;")
        
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
        self.status_indicator.setStyleSheet("background-color: yellow; border-radius: 8px;")
        self.status_label.setText("Testing connection...")
        
        # Run connection test in a separate thread to avoid UI freezing
        def run_test():
            connected = self.api.test_connection()
            
            # Update UI from main thread
            QtCore.QMetaObject.invokeMethod(
                self, 
                "update_connection_status", 
                QtCore.Qt.QueuedConnection, 
                QtCore.Q_ARG(bool, connected)
            )
        
        threading.Thread(target=run_test).start()
    
    @QtCore.Slot(bool)
    def update_connection_status(self, connected):
        """Update UI based on connection status"""
        self.setEnabled(True)
        
        if connected:
            self.status_indicator.setStyleSheet("background-color: green; border-radius: 8px;")
            self.status_label.setText("Connected to API")
            
            # Load weapon types
            self.load_weapon_types()
        else:
            self.status_indicator.setStyleSheet("background-color: red; border-radius: 8px;")
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
        prev_btn.clicked.connect(lambda: self.navigate_parts(weapon_type, part_type, -1))
        
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
            "next_btn": next_btn
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
        
        # Get parts from API
        def fetch_parts():
            parts = self.api.get_weapon_parts(weapon_type, part_type, page=page)
            
            # Update UI from main thread
            QtCore.QMetaObject.invokeMethod(
                self, 
                "update_parts_display", 
                QtCore.Qt.QueuedConnection, 
                QtCore.Q_ARG(str, part_type),
                QtCore.Q_ARG(object, parts)
            )
        
        # Update UI to show loading
        if part_type in self.part_widgets:
            widgets = self.part_widgets[part_type]
            widgets["info"].setText("Loading...")
        
        # Run in a separate thread to avoid UI freezing
        threading.Thread(target=fetch_parts).start()
    
    @QtCore.Slot(str, object)
    def update_parts_display(self, part_type, parts_data):
        """Update the parts display with loaded data"""
        if part_type not in self.part_widgets:
            return
        
        widgets = self.part_widgets[part_type]
        
        # Check if we have parts
        if isinstance(parts_data, list) and parts_data:
            # Store first part in the current selection
            part = parts_data[0]
            self.selected_parts[part_type] = part.get("id")
            
            # Display part info
            name = part.get("metadata", {}).get("name", "Unknown")
            widgets["info"].setText(name)
            
            # Update preview (if available)
            self.update_part_preview(part_type, part)
            
            # Store all parts for this type
            self.part_models[part_type] = parts_data
            
            # Enable/disable navigation buttons
            widgets["prev_btn"].setEnabled(self.current_pages[part_type] > 1)
            widgets["next_btn"].setEnabled(len(parts_data) >= 10)  # Assuming page size of 10
            
            # Update pagination status
            self.has_more_pages[part_type] = len(parts_data) >= 10
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
        """Update the preview for a part"""
        if part_type not in self.part_widgets:
            return
        
        # For now, just use a colored preview based on part type
        # In a real implementation, this would load thumbnail images from the API
        
        colors = {
            "handle": "#8B4513",    # Brown
            "blade": "#C0C0C0",     # Silver
            "guard": "#FFD700",     # Gold
            "pommel": "#B87333",    # Copper
            "head": "#A52A2A",      # Brown-red
            "shaft": "#A0522D",     # Sienna
            "limbs": "#DEB887",     # Burlywood
            "string": "#F5F5DC",    # Beige
            "body": "#CD853F",      # Peru
            "border": "#D2B48C",    # Tan
            "boss": "#DAA520",      # Goldenrod
            "barrel": "#696969",    # DimGray
            "trigger": "#708090",   # SlateGray
            "magazine": "#778899",  # LightSlateGray
            "sight": "#2F4F4F",     # DarkSlateGray
            "stock": "#5F9EA0",     # CadetBlue
            "grip": "#556B2F",      # DarkOliveGreen
        }
        
        color = colors.get(part_type, "#888888")
        
        pixmap = QtGui.QPixmap(120, 120)
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
        
        # Set the preview image
        self.part_widgets[part_type]["preview"].setPixmap(pixmap)
    
    def navigate_parts(self, weapon_type, part_type, direction):
        """Navigate through parts (previous/next)"""
        if part_type not in self.part_models:
            return
        
        # If we have cached parts, cycle through them
        parts = self.part_models.get(part_type, [])
        
        if parts:
            # Find current selected index
            current_id = self.selected_parts.get(part_type)
            current_index = -1
            
            for i, part in enumerate(parts):
                if part.get("id") == current_id:
                    current_index = i
                    break
            
            if current_index >= 0:
                # Calculate new index
                new_index = current_index + direction
                
                # If we need to load more pages
                if new_index < 0:
                    # Load previous page if available
                    if self.current_pages[part_type] > 1:
                        self.current_pages[part_type] -= 1
                        self.load_parts(weapon_type, part_type)
                    return
                
                if new_index >= len(parts):
                    # Load next page if available
                    if self.has_more_pages[part_type]:
                        self.current_pages[part_type] += 1
                        self.load_parts(weapon_type, part_type)
                    return
                
                # Update selection to the new index
                new_part = parts[new_index]
                self.selected_parts[part_type] = new_part.get("id")
                
                # Update display
                if part_type in self.part_widgets:
                    widgets = self.part_widgets[part_type]
                    name = new_part.get("metadata", {}).get("name", "Unknown")
                    widgets["info"].setText(name)
                    self.update_part_preview(part_type, new_part)
    
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
                self, 
                "Missing Parts", 
                "Please select parts for your weapon first."
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
            
            assembly_parts.append({
                "model_id": part_id,
                "part_type": part_type,
                "position": position,
                "rotation": {"x": 0, "y": 0, "z": 0},
                "scale": {"x": 1, "y": 1, "z": 1}
            })
        
        assembly_data = {
            "name": f"Generated {weapon_type.capitalize()}",
            "description": f"Generated using Weapon Generator HDA",
            "weapon_type": weapon_type,
            "parts": assembly_parts,
            "created_at": None,  # Will be set by API
            "updated_at": None,  # Will be set by API
            "tags": ["hda_generated"]
        }
        
        # Disable UI during process
        self.setEnabled(False)
        self.status_label.setText("Generating weapon...")
        
        # Show progress dialog
        progress = QtWidgets.QProgressDialog("Generating weapon...", "Cancel", 0, 100, self)
        progress.setWindowModality(QtCore.Qt.WindowModal)
        progress.setMinimumDuration(0)
        progress.setValue(10)
        
        # Download and assemble parts in a separate thread
        def create_weapon():
            try:
                # Create assembly in API
                # In a full implementation, we'd use this, but for now we'll just download the models
                # assembly_result = self.api.create_assembly(assembly_data)
                
                # Update progress
                QtCore.QMetaObject.invokeMethod(
                    self, 
                    "assemble_weapon_parts", 
                    QtCore.Qt.QueuedConnection, 
                    QtCore.Q_ARG(object, model_files),
                    QtCore.Q_ARG(object, assembly_data)
                )
            except Exception as e:
                # Handle errors
                QtCore.QMetaObject.invokeMethod(
                    self, 
                    "generation_finished", 
                    QtCore.Qt.QueuedConnection, 
                    QtCore.Q_ARG(bool, False),
                    QtCore.Q_ARG(str, str(e))
                )
        
        # Run in a separate thread to avoid freezing the UI
        threading.Thread(target=create_weapon).start()
    
    @QtCore.Slot(bool, str)
    def generation_finished(self, success, message=""):
        """Handle weapon generation completion"""
        # Re-enable UI
        self.setEnabled(True)
        
        if success:
            self.status_label.setText("Weapon generated successfully")
        else:
            self.status_label.setText(f"Generation failed: {message}")
            QtWidgets.QMessageBox.warning(
                self, 
                "Generation Failed", 
                f"Failed to generate weapon: {message}"
            )
    
    @QtCore.Slot(object, object)
    def assemble_weapon_parts(self, model_files, assembly_data):
        """Assemble downloaded weapon parts in Houdini"""
        try:
            # Get current node (HDA)
            node = hou.pwd()
            if not node:
                # If not in HDA context, try to get parent
                node = hou.node("/obj")
            
            # Create a new null node to hold our output
            weapon_node = node.createOutputNode("null", "OUTPUT_Weapon")
            
            # Create merge node to combine parts
            merge_node = weapon_node.createInputNode("merge", "MERGE_Parts")
            
            # Add each part
            input_index = 0
            
            # First make sure the output directory exists
            out_dir = os.path.join(os.path.dirname(node.path()), "weapon_parts")
            if not os.path.exists(out_dir):
                try:
                    os.makedirs(out_dir)
                except:
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
                
                # Import model file
                import_node = merge_node.createInputNode("file", f"FILE_{part_type}")
                
                # Set file path
                import_node.parm("file").set(model_path)
                
                # Create transform node for positioning
                xform_node = import_node.createInputNode("xform", f"XFORM_{part_type}")
                
                # Set transform parameters
                xform_node.parmTuple("t").set([position.get("x", 0), position.get("y", 0), position.get("z", 0)])
                xform_node.parmTuple("r").set([rotation.get("x", 0), rotation.get("y", 0), rotation.get("z", 0)])
                xform_node.parmTuple("s").set([scale.get("x", 1), scale.get("y", 1), scale.get("z", 1)])
                
                # Connect to merge node
                merge_node.setInput(input_index, xform_node)
                input_index += 1
            
            # Cook the nodes
            weapon_node.cook(force=True)
            
            # Signal completion
            self.generation_finished(True)
            
            # Select the output node
            weapon_node.setSelected(True)
            
        except Exception as e:
            self.generation_finished(False, str(e))


# -----------------------------------------------------------------------------
# HDA Interface Functions
# -----------------------------------------------------------------------------

def onCreateInterface():
    """Create the HDA UI when the node is created or the tab is opened"""
    # Get the current node
    node = hou.pwd()
    
    # Create the UI widget
    widget = WeaponGeneratorWidget()
    
    return widget


def onNodeCreated():
    """Called when the node is first created"""
    node = hou.pwd()
    
    # Create default parameters if they don't exist
    if not node.parm("api_url"):
        # Create parameter template group
        ptg = node.parmTemplateGroup()
        
        # API URL parameter
        api_url_parm = hou.StringParmTemplate(
            "api_url", 
            "API URL", 
            1, 
            default_value=["http://localhost:8000"]
        )
        api_url_parm.setHelp("URL of the 3D Weapon Assembly API")
        
        # Output path parameter
        output_path_parm = hou.StringParmTemplate(
            "output_path", 
            "Output Path", 
            1, 
            default_value=["$HIP/geo/weapons"]
        )
        output_path_parm.setHelp("Path where assembled weapons will be saved")
        
        # Add parameters to template group
        ptg.addParmTemplate(api_url_parm)
        ptg.addParmTemplate(output_path_parm)
        
        # Set the parameter template group
        node.setParmTemplateGroup(ptg)
invokeMethod(
                    progress, 
                    "setValue", 
                    QtCore.Qt.QueuedConnection, 
                    QtCore.Q_ARG(int, 20)
                )
                
                # Download all selected parts
                model_files = {}
                i = 0
                total_parts = len(self.selected_parts)
                
                for part_type, part_id in self.selected_parts.items():
                    # Skip if cancelled
                    if progress.wasCanceled():
                        QtCore.QMetaObject.invokeMethod(
                            self, 
                            "generation_finished", 
                            QtCore.Qt.QueuedConnection, 
                            QtCore.Q_ARG(bool, False),
                            QtCore.Q_ARG(str, "Cancelled by user")
                        )
                        return
                    
                    # Download the model
                    model_path = self.api.download_model(part_id)
                    if model_path:
                        model_files[part_type] = model_path
                    
                    # Update progress
                    i += 1
                    progress_value = 20 + int(60 * (i / total_parts))
                    QtCore.QMetaObject.invokeMethod(
                        progress, 
                        "setValue", 
                        QtCore.Qt.QueuedConnection, 
                        QtCore.Q_ARG(int, progress_value)
                    )
                
                # Process is complete, use Houdini to assemble the parts
                QtCore.QMetaObject.invokeMethod(
                    progress, 
                    "setValue", 
                    QtCore.Qt.QueuedConnection, 
                    QtCore.Q_ARG(int, 90)
                )
                
                QtCore.QMetaObject.