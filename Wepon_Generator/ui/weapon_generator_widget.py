"""
Weapon Generator Widget
---------------------
Main UI widget for the weapon generator interface.
"""

import hou
from PySide2 import QtCore, QtWidgets, QtGui
from PySide2.QtNetwork import QNetworkAccessManager, QNetworkReply, QNetworkRequest
import threading
import requests
from .weapon_part_upload_widget import WeaponPartUploadWidget
from .weapon_assembly import WeaponAssemblyAPI


class WeaponGeneratorWidget(QtWidgets.QWidget):
    """Widget for the Weapon Generator UI"""

    # Signal definitions
    connectionStatusChanged = QtCore.Signal(bool)
    partsLoaded = QtCore.Signal(str, object)
    generationFinished = QtCore.Signal(bool, str)
    weaponAssembled = QtCore.Signal(object, object)
    progressUpdated = QtCore.Signal(int)
    refreshRequested = QtCore.Signal()
    civilizationsLoaded = QtCore.Signal(object)
    analysisCompleted = QtCore.Signal(object)
    analysisError = QtCore.Signal()
    recommendationsReceived = QtCore.Signal(object)

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
        self.refreshRequested.connect(self.refresh_parts)
        self.civilizationsLoaded.connect(self.update_civilizations_list)
        # Test API connection and initialize
        self.initialize()

    def update_progress(self, value):
        """Update the progress dialog - triggered from signal"""
        if hasattr(self, "progress_dialog") and self.progress_dialog:
            self.progress_dialog.setValue(value)

    def create_ui(self):
        """Create the user interface with civilization selection"""
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
        self.url_label = QtWidgets.QLabel("Context API URL:")
        self.url_input = QtWidgets.QLineEdit("http://localhost:8002")
        self.url_input.setPlaceholderText("http://localhost:8002")
        self.connect_button = QtWidgets.QPushButton("Connect")
        self.connect_button.clicked.connect(self.test_connection)

        self.url_layout.addWidget(self.url_label)
        self.url_layout.addWidget(self.url_input, 1)
        self.url_layout.addWidget(self.connect_button)

        # Civilization selection section
        self.civ_layout = QtWidgets.QHBoxLayout()
        self.civ_label = QtWidgets.QLabel("Civilization:")
        self.civ_combo = QtWidgets.QComboBox()
        self.civ_combo.setMinimumWidth(200)
        self.civ_combo.currentIndexChanged.connect(self.on_civilization_changed)

        self.load_civs_button = QtWidgets.QPushButton("Load Civilizations")
        self.load_civs_button.clicked.connect(self.load_civilizations)

        self.analyze_button = QtWidgets.QPushButton("Analyze Context")
        self.analyze_button.clicked.connect(self.analyze_civilization)
        self.analyze_button.setEnabled(False)

        self.civ_layout.addWidget(self.civ_label)
        self.civ_layout.addWidget(self.civ_combo, 1)
        self.civ_layout.addWidget(self.load_civs_button)
        self.civ_layout.addWidget(self.analyze_button)

        # Context info display
        self.context_info = QtWidgets.QTextEdit()
        self.context_info.setMaximumHeight(80)
        self.context_info.setPlaceholderText(
            "Select a civilization to see weapon context analysis..."
        )
        self.context_info.setReadOnly(True)
        
        self.analysisCompleted.connect(self.display_civilization_analysis)
        self.analysisError.connect(self.display_analysis_error)
        self.recommendationsReceived.connect(self.display_recommendations)

        # Weapon type selection
        self.type_layout = QtWidgets.QHBoxLayout()
        self.type_label = QtWidgets.QLabel("Weapon Type:")
        self.type_combo = QtWidgets.QComboBox()
        self.type_combo.setMinimumWidth(150)
        self.type_combo.currentIndexChanged.connect(self.on_weapon_type_changed)

        self.recommendations_button = QtWidgets.QPushButton("Get Recommendations")
        self.recommendations_button.clicked.connect(self.get_weapon_recommendations)
        self.recommendations_button.setEnabled(False)

        self.type_layout.addWidget(self.type_label)
        self.type_layout.addWidget(self.type_combo)
        self.type_layout.addWidget(self.recommendations_button)
        self.type_layout.addStretch()

        # Parts selection area
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

        self.refresh_button = QtWidgets.QPushButton("Refresh Parts")
        self.refresh_button.setToolTip("Refresh available parts from the server")
        self.refresh_button.clicked.connect(self.refresh_all_parts)

        self.action_layout.addWidget(self.reset_button)
        self.action_layout.addWidget(self.refresh_button)
        self.action_layout.addStretch()
        self.action_layout.addWidget(self.create_button)

        # Add all layouts to main layout
        main_layout.addLayout(self.status_layout)
        main_layout.addLayout(self.url_layout)
        main_layout.addLayout(self.civ_layout)
        main_layout.addWidget(self.context_info)
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

    def load_civilizations(self):
        """Load civilizations from CivAPI via CivContextAPI"""
        self.status_label.setText("Loading civilizations...")
        threading.Thread(target=self._fetch_civilizations).start()

    def _fetch_civilizations(self):
        """Fetch civilizations in background thread"""
        try:
            # Call CivAPI directly to get civilizations list
            civ_api_url = "http://localhost:8001"  # CivAPI URL
            response = requests.get(f"{civ_api_url}/civilizations/", timeout=10)

            if response.status_code == 200:
                data = response.json()
                civilizations = data.get("civilizations", [])
                self.civilizationsLoaded.emit(civilizations)
            else:
                print(f"Error loading civilizations: {response.status_code}")
                self.civilizationsLoaded.emit([])
        except Exception as e:
            print(f"Error fetching civilizations: {str(e)}")
            self.civilizationsLoaded.emit([])

    def update_civilizations_list(self, civilizations):
        """Update the civilizations dropdown"""
        self.civilizations = civilizations
        self.civ_combo.clear()
        self.civ_combo.addItem("Select a civilization...", None)

        for civ in civilizations:
            name = civ.get("metadata", {}).get("name", "Unknown")
            civ_id = civ.get("id")
            tech_level = civ.get("metadata", {}).get("technology_level", "unknown")
            gov_type = civ.get("metadata", {}).get("government_type", "unknown")

            display_text = f"{name} ({tech_level}, {gov_type})"
            self.civ_combo.addItem(display_text, civ_id)

        self.status_label.setText(f"Loaded {len(civilizations)} civilizations")

    def on_civilization_changed(self, index):
        """Handle civilization selection change"""
        if index <= 0:  # "Select a civilization..." option
            self.current_civilization = None
            self.api.set_civilization_context(None)
            self.analyze_button.setEnabled(False)
            self.recommendations_button.setEnabled(False)
            self.context_info.clear()
            self.type_combo.clear()
            self.clear_parts_ui()
            return

        civ_id = self.civ_combo.itemData(index)
        if civ_id:
            self.current_civilization = civ_id
            self.api.set_civilization_context(civ_id)
            self.analyze_button.setEnabled(True)
            self.recommendations_button.setEnabled(True)

            # Auto-analyze the civilization
            self.analyze_civilization()

    def analyze_civilization(self):
        """Analyze the selected civilization for weapon context"""
        if not self.current_civilization:
            return

        self.status_label.setText("Analyzing civilization context...")
        threading.Thread(target=self._analyze_civilization).start()

    def _analyze_civilization(self):
        """Analyze civilization in background thread"""
        try:
            analysis = self.api.analyze_civilization_context()
            if analysis:
                self.analysisCompleted.emit(analysis)  # ← Simple signal emission
            else:
                self.analysisError.emit()
        except Exception as e:
            print(f"Error analyzing civilization: {str(e)}")
            self.analysisError.emit()

    def display_civilization_analysis(self, analysis):
        """Display the civilization analysis results"""
        try:
            summary = analysis.get("summary", {})
            civ_name = summary.get("civilization_name", "Unknown")
            tech_level = summary.get("technology_level", "unknown")
            gov_type = summary.get("government_type", "unknown")
            military = summary.get("military_structure", "unknown")
            allowed_weapons = summary.get("allowed_weapon_types", [])
            aesthetics = summary.get("aesthetic_preferences", [])

            context_text = f"""Civilization: {civ_name}
Technology: {tech_level} | Government: {gov_type} | Military: {military}
Allowed Weapons: {', '.join(allowed_weapons)}
Aesthetic Preferences: {', '.join(aesthetics)}"""

            self.context_info.setText(context_text)

            # Update weapon types based on analysis
            self.load_weapon_types_from_analysis(allowed_weapons)

            self.status_label.setText("Civilization analysis complete")
        except Exception as e:
            print(f"Error displaying analysis: {str(e)}")
            self.display_analysis_error()

    def display_analysis_error(self):
        """Display error message for analysis"""
        self.context_info.setText("Error analyzing civilization context")
        self.status_label.setText("Analysis failed")

    def load_weapon_types_from_analysis(self, allowed_weapons):
        """Load weapon types based on civilization analysis"""
        self.type_combo.clear()

        if allowed_weapons:
            for weapon_type in allowed_weapons:
                display_name = weapon_type.replace("_", " ").title()
                self.type_combo.addItem(display_name, weapon_type)
        else:
            # Fallback to all weapon types
            weapon_types = self.api.get_weapon_types()
            for weapon_type in weapon_types:
                display_name = weapon_type.replace("_", " ").title()
                self.type_combo.addItem(display_name, weapon_type)

    def get_weapon_recommendations(self):
        """Get weapon recommendations for the current civilization"""
        if not self.current_civilization:
            QtWidgets.QMessageBox.warning(
                self, "No Civilization", "Please select a civilization first."
            )
            return

        weapon_type = None
        if self.type_combo.currentIndex() >= 0:
            weapon_type = self.type_combo.currentData()

        self.status_label.setText("Getting weapon recommendations...")
        threading.Thread(target=self._get_recommendations, args=(weapon_type,)).start()

    def _get_recommendations(self, weapon_type):
        """Get recommendations in background thread"""
        try:
            recommendations = self.api.get_weapon_recommendations(
                weapon_type=weapon_type, limit=20, min_compatibility=0.3
            )

            self.recommendationsReceived.emit(recommendations)
        except Exception as e:
            print(f"Error getting recommendations: {str(e)}")

    def display_recommendations(self, recommendations):
        """Display weapon recommendations"""
        if not recommendations:
            QtWidgets.QMessageBox.information(
                self,
                "No Recommendations",
                "No weapon recommendations found for this civilization.",
            )
            return

        # Create a dialog to show recommendations
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle("Weapon Recommendations")
        dialog.setMinimumSize(600, 400)

        layout = QtWidgets.QVBoxLayout(dialog)

        # Create a list widget
        list_widget = QtWidgets.QListWidget()

        for rec in recommendations:
            weapon_name = rec.get("metadata", {}).get("name", "Unknown")
            compatibility = rec.get("compatibility_score", 0.0)
            reasons = rec.get("reasons", [])

            item_text = f"{weapon_name} (Compatibility: {compatibility:.2f})\nReasons: {', '.join(reasons)}"
            list_widget.addItem(item_text)

        layout.addWidget(list_widget)

        # Add close button
        close_button = QtWidgets.QPushButton("Close")
        close_button.clicked.connect(dialog.accept)
        layout.addWidget(close_button)

        dialog.exec_()
        self.status_label.setText(f"Found {len(recommendations)} recommendations")

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
        if not weapon_type:
            return

        # Get part types for the selected weapon type
        part_types = self.api.get_part_types(weapon_type)

        # Create UI for each part type
        for part_type in part_types:
            self.add_part_selection(weapon_type, part_type)

    def clear_parts_ui(self):
        """Clear the parts UI layout"""
        while self.parts_layout.count():
            item = self.parts_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self.part_widgets = {}
        self.current_pages = {}
        self.has_more_pages = {}

    def refresh_all_parts(self):
        """Refresh all parts by clearing cache and reloading data"""
        self.status_label.setText("Refreshing parts...")
        self.api.clear_cache()
        self.refreshRequested.emit()
        self.status_label.setText("Parts refreshed")

    def refresh_parts(self):
        """Refresh current weapon type parts"""
        weapon_type_index = self.type_combo.currentIndex()
        if weapon_type_index < 0:
            return

        old_selections = self.selected_parts.copy()
        self.on_weapon_type_changed(weapon_type_index)
        self.selected_parts = old_selections

    # Include the rest of the methods from the original widget...
    # (add_part_selection, load_parts, update_parts_display, etc.)
    # These remain largely the same but now use the updated API

    def update_progress(self, value):
        """Update the progress dialog"""
        if hasattr(self, "progress_dialog") and self.progress_dialog:
            self.progress_dialog.setValue(value)

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
        # Create a simple icon with text
        pixmap = QtGui.QPixmap(120, 120)
        pixmap.fill(QtCore.Qt.transparent)

        painter = QtGui.QPainter(pixmap)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)

        # Draw a subtle background
        painter.setBrush(QtGui.QBrush(QtGui.QColor(70, 70, 70, 180)))
        painter.setPen(QtCore.Qt.NoPen)
        painter.drawRoundedRect(5, 5, 110, 110, 8, 8)

        # Draw text
        painter.setPen(QtGui.QPen(QtGui.QColor("#BBBBBB")))
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
        """Fetch parts from the API for the given weapon type and part type"""
        parts = self.api.get_weapon_parts(weapon_type, part_type, page)
        self.partsLoaded.emit(part_type, parts)

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
            if (
                part_type not in self.selected_parts
                or not self.selected_parts[part_type]
            ):
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
            widgets["prev_btn"].setEnabled(
                self.current_pages[part_type] > 1 or len(parts_data) > 1
            )
            widgets["next_btn"].setEnabled(
                self.has_more_pages[part_type] or len(parts_data) > 1
            )

            # Update pagination status
            self.has_more_pages[part_type] = (
                len(parts_data) >= 10
            )  # Assuming page size of 10
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
            # Use QNetworkAccessManager for async image loading without freezing UI
            if not hasattr(self, "network_manager"):
                self.network_manager = QNetworkAccessManager()
                self.network_manager.finished.connect(self.handle_network_response)

            # Initialize request tracking dictionary if not exists
            if not hasattr(self, "request_data"):
                self.request_data = {}

            # Show loading indicator while waiting for image
            spinner_pixmap = self.create_loading_indicator()
            preview_label.setPixmap(spinner_pixmap)

            # Get the icon URL
            icon_url = f"{self.api.base_url}/models/icons/{part_id}"
            url = QtCore.QUrl(icon_url)
            request = QNetworkRequest(url)

            # Store request data in a dictionary using the URL as key
            url_str = url.toString()
            self.request_data[url_str] = {"part_type": part_type, "part_id": part_id}

            # Debug info
            print(f"Fetching icon for {part_type} (ID: {part_id}): {icon_url}")

            # Send the request
            self.network_manager.get(request)
        except Exception as e:
            print(f"Error fetching icon: {str(e)}")
            self._create_colored_preview(placeholder, part_type, part)
            preview_label.setPixmap(placeholder)

    def handle_network_response(self, reply):
        """Handle the network response for image downloads"""
        # Get the URL used in the request
        url = reply.request().url().toString()

        # Get the stored data from our tracking dictionary
        request_info = getattr(self, "request_data", {}).get(url, {})
        part_type = request_info.get("part_type")
        part_id = request_info.get("part_id")

        # Clean up the request from our tracking dictionary
        if url in getattr(self, "request_data", {}):
            del self.request_data[url]

        # If we can't find the part_type, we can't proceed
        if not part_type or part_type not in self.part_widgets:
            print(f"Warning: Could not determine part type for reply from URL: {url}")
            return

        if part_type not in self.part_widgets:
            return

        preview_label = self.part_widgets[part_type]["preview"]
        error = reply.error()

        # Debug info
        print(f"Received icon response for {part_type} (ID: {part_id}), error: {error}")

        if error == QNetworkReply.NoError:
            try:
                # Read the image data
                image_data = reply.readAll()

                # Create a QImage from the data
                image = QtGui.QImage()
                if image.loadFromData(image_data):
                    # If the image loaded successfully, convert to a pixmap
                    pixmap = QtGui.QPixmap.fromImage(image)

                    # Scale to fit the preview label while maintaining aspect ratio
                    pixmap = pixmap.scaled(
                        120,
                        120,
                        QtCore.Qt.KeepAspectRatio,
                        QtCore.Qt.SmoothTransformation,
                    )

                    # Set the pixmap on the preview label
                    preview_label.setPixmap(pixmap)

                    # Debug info
                    print(
                        f"Successfully displayed icon for {part_type} (ID: {part_id})"
                    )
                else:
                    raise Exception("Invalid image data")
            except Exception as e:
                print(f"Error processing icon: {str(e)}")

                # Find the part in our current data
                part = None
                for p in self.part_models.get(part_type, []):
                    if p.get("id") == part_id:
                        part = p
                        break

                # Create a fallback preview
                placeholder = QtGui.QPixmap(120, 120)
                placeholder.fill(QtCore.Qt.transparent)
                if part:
                    self._create_colored_preview(placeholder, part_type, part)
                else:
                    # Default fallback if we can't find the part data
                    self.set_default_preview(preview_label)
                    return

                preview_label.setPixmap(placeholder)
        else:
            print(f"Network error: {reply.errorString()}")

            # Find the part in our current data
            part = None
            for p in self.part_models.get(part_type, []):
                if p.get("id") == part_id:
                    part = p
                    break

            # Create a fallback preview
            placeholder = QtGui.QPixmap(120, 120)
            placeholder.fill(QtCore.Qt.transparent)
            if part:
                self._create_colored_preview(placeholder, part_type, part)
            else:
                # Default fallback if we can't find the part data
                self.set_default_preview(preview_label)
                return

            preview_label.setPixmap(placeholder)

    def create_loading_indicator(self):
        """Create a loading spinner indicator"""
        pixmap = QtGui.QPixmap(120, 120)
        pixmap.fill(QtCore.Qt.transparent)

        painter = QtGui.QPainter(pixmap)

        # Set up the painter with anti-aliasing
        painter.setRenderHint(QtGui.QPainter.Antialiasing)

        # Create a light gray outline circle
        painter.setPen(QtGui.QPen(QtGui.QColor("#888888"), 2))
        painter.setBrush(QtGui.QBrush(QtCore.Qt.NoBrush))
        painter.drawEllipse(40, 40, 40, 40)

        # Create a blue arc to indicate loading
        pen = QtGui.QPen(QtGui.QColor("#3498db"), 3)
        painter.setPen(pen)
        # Draw an arc from 0 to 120 degrees
        painter.drawArc(40, 40, 40, 40, 0, 120 * 16)  # Qt uses 1/16th of a degree

        # Add "Loading..." text
        painter.setPen(QtGui.QPen(QtGui.QColor("#888888")))
        painter.setFont(QtGui.QFont("Arial", 10))
        painter.drawText(pixmap.rect(), QtCore.Qt.AlignCenter, "Loading...")

        painter.end()
        return pixmap

    def _create_colored_preview(self, pixmap, part_type, part):
        """Create a colored preview with text as fallback"""
        # Define distinct colors for different part types
        colors = {
            "handle": "#8B4513",  # Brown
            "grip": "#A0522D",  # Sienna
            "blade": "#C0C0C0",  # Silver
            "guard": "#B8860B",  # DarkGoldenrod
            "pommel": "#CD853F",  # Peru
            "head": "#A52A2A",  # Brown
            "shaft": "#D2B48C",  # Tan
            "stock": "#5F9EA0",  # CadetBlue
            "barrel": "#708090",  # SlateGray
            "body": "#4682B4",  # SteelBlue
        }

        # Get color based on part type or use default
        color = colors.get(part_type, "#888888")
        pixmap.fill(QtGui.QColor(color))

        # Create a painter to add text on the pixmap
        painter = QtGui.QPainter(pixmap)
        painter.setPen(QtGui.QPen(QtCore.Qt.white))
        painter.setFont(QtGui.QFont("Arial", 10))

        # Get the part name from metadata
        name = part.get("metadata", {}).get("name", "Unknown")

        # Truncate long names
        if len(name) > 20:
            name = name[:17] + "..."

        # Draw name centered on the pixmap
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
        print(
            f"Navigate {part_type}: {len(parts)} parts available, direction: {direction}"
        )

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
                    print(
                        f"Loading previous page for {part_type}: page {self.current_pages[part_type]}"
                    )
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
                    print(
                        f"Loading next page for {part_type}: page {self.current_pages[part_type]}"
                    )
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

        # Store a reference to the progress dialog
        self.progress_dialog = self.progress

        # Download and assemble parts in a separate thread
        threading.Thread(target=self._create_weapon, args=(assembly_data,)).start()

    def _create_weapon(self, assembly_data):
        """Create a weapon in a background thread"""
        try:
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

            # Progress is complete, update progress
            self.progressUpdated.emit(90)

            # Signal to assemble parts in the main thread
            self.weaponAssembled.emit(model_files, assembly_data)

            self.progressUpdated.emit(100)
            self.generationFinished.emit(True, "Weapon created successfully!")
        except Exception as e:
            print(f"Error in on_weapon_assembled: {str(e)}")
            import traceback

            traceback.print_exc()
            self.generationFinished.emit(False, str(e))

    def on_generation_finished(self, success, message=""):
        """Handle weapon generation completion - triggered from signal"""
        # Re-enable UI
        self.setEnabled(True)

        # Make sure to close the progress dialog
        if hasattr(self, "progress") and self.progress:
            self.progress.setValue(100)
            self.progress.close()

        if success:
            self.status_label.setText("Weapon generated successfully")
            QtWidgets.QMessageBox.information(
                self, "Success", message or "Weapon generated successfully"
            )
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

            # Print node path for debugging
            print(f"Parent node: {node.path()}")
            self.progressUpdated.emit(60)

            # Clear existing nodes first
            for child in node.children():
                if (
                    child.name().startswith("file")
                    or child.name().startswith("python")
                    or child.name() == "weapon_output"
                    or child.name() == "output0"
                ):
                    try:
                        child.destroy()
                    except hou.OperationFailed:
                        pass

            # Create file nodes for each part
            file_nodes = []
            for i, (part_type, model_path) in enumerate(model_files.items()):
                file_node = node.createNode("file", f"file{i+1}")
                file_node.parm("file").set(model_path)
                file_node.setPosition([i * 3 - (len(model_files) * 1.5), 0])
                file_node.setComment(part_type)
                file_nodes.append(file_node)

            # Determine how many Python SOP nodes needed (max 4 inputs each)
            total_parts = len(file_nodes)

            # Handle special cases for 2-5 parts first
            if total_parts <= 2:
                # If only 1 or 2 parts, use a single Python node
                distribution = [total_parts]
            elif total_parts == 3:
                # If 3 parts, use one Python node
                distribution = [3]
            elif total_parts == 4:
                # If 4 parts, use one Python node
                distribution = [4]
            elif total_parts == 5:
                # If 5 parts, use two Python nodes: 3 parts, 2 parts
                distribution = [3, 2]
            else:
                # For 6+ parts, distribute as evenly as possible while maintaining
                # minimum 2 inputs per node
                distribution = []
                remaining = total_parts
                max_inputs = 4  # Maximum inputs per Python node

                while remaining > 0:
                    if remaining <= max_inputs:
                        # Last node gets all remaining parts
                        distribution.append(remaining)
                        remaining = 0
                    elif remaining <= 2 * max_inputs:
                        # If we have between max_inputs+1 and 2*max_inputs parts remaining,
                        # distribute them evenly across 2 nodes
                        parts_per_node = (remaining + 1) // 2  # Ceiling division
                        distribution.append(parts_per_node)
                        remaining -= parts_per_node
                    else:
                        # Otherwise, use max_inputs for this node
                        distribution.append(max_inputs)
                        remaining -= max_inputs

            print(f"Part distribution across Python nodes: {distribution}")

            # Create the Python script - using dedent to remove ALL indentation
            # The key is to use a raw string with no indentation at all
            python_code = """import hou
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
    """

            # Create Python nodes
            python_nodes = []
            start_idx = 0
            for i, count in enumerate(distribution):
                python_node = node.createNode("python", f"python{i+1}")
                python_node.setPosition([(i * 6) - (len(distribution) * 3), -3])
                python_node.parm("python").set(python_code)

                # Connect file nodes according to distribution
                for j in range(count):
                    if start_idx + j < len(file_nodes):
                        python_node.setInput(j, file_nodes[start_idx + j])

                start_idx += count
                python_nodes.append(python_node)

            # Create final Python node if needed (more than one Python node)
            if len(python_nodes) > 1:
                final_python = node.createNode("python", "python_final")
                final_python.setPosition([0, -6])
                final_python.parm("python").set(python_code)

                # Connect all python nodes
                for i, py_node in enumerate(python_nodes):
                    final_python.setInput(i, py_node)

                output_source = final_python
            else:
                output_source = python_nodes[0]

            # Create output chain
            weapon_out = node.createNode("null", "weapon_output")
            weapon_out.setPosition([0, -9])
            weapon_out.setInput(0, output_source)

            output = node.createNode("output", "output0")
            output.setPosition([0, -12])
            output.setInput(0, weapon_out)

            # Set display flags
            output.setDisplayFlag(True)
            output.setRenderFlag(True)

            # Layout network
            node.layoutChildren()

            # Select output node
            weapon_out.setSelected(True)

            self.progressUpdated.emit(100)
            self.generationFinished.emit(True, "Weapon created successfully!")

        except Exception as e:
            print(f"Error in on_weapon_assembled: {str(e)}")
            import traceback

            traceback.print_exc()
            self.generationFinished.emit(False, str(e))


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

    # Connect signals for refreshing parts list after upload
    upload_widget.uploadCompleted.connect(
        lambda success, msg: generator_widget.refresh_all_parts() if success else None
    )

    # Add tabs
    tab_widget.addTab(generator_widget, "Generate Weapon")
    tab_widget.addTab(upload_widget, "Upload Parts")

    layout.addWidget(tab_widget)

    # Show the dialog
    dialog.exec_()

    return dialog
