import hou
import requests
import json
import webbrowser
import os
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import threading
from PySide2 import QtCore, QtWidgets
from datetime import datetime, timedelta
from functools import partial


class OAuthCallbackHandler(BaseHTTPRequestHandler):
    """Handle OAuth callback from ClickUp"""

    def do_GET(self):
        """Handle GET request from OAuth callback"""
        parsed_path = urlparse(self.path)
        params = parse_qs(parsed_path.query)

        if "code" in params:
            self.server.auth_code = params["code"][0]
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(
                b"""
                <html>
                <body>
                <h1>Authentication successful!</h1>
                <p>You can close this window and return to Houdini.</p>
                <script>window.close();</script>
                </body>
                </html>
            """
            )
        else:
            self.send_response(400)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(b"Authentication failed. No code received.")

    def log_message(self, format, *args):
        """Suppress server logs"""
        pass


class ClickUpAuthenticator:
    """Handle ClickUp OAuth authentication flow"""

    def __init__(self, client_id, client_secret, redirect_uri="http://localhost:8888"):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.access_token = None
        self.refresh_token = None
        self.token_expires_at = 0

    def authenticate(self):
        """Start OAuth authentication flow"""
        # Start local server to handle callback
        server = HTTPServer(("localhost", 8888), OAuthCallbackHandler)
        server.auth_code = None

        # Start server in a separate thread
        server_thread = threading.Thread(
            target=self._handle_auth_server, args=(server,)
        )
        server_thread.daemon = True
        server_thread.start()

        # Open browser for authentication
        auth_url = (
            f"https://app.clickup.com/api?client_id={self.client_id}"
            f"&redirect_uri={self.redirect_uri}"
        )
        webbrowser.open(auth_url)

        # Wait for authentication code
        timeout = 120  # 2 minutes timeout
        start_time = time.time()
        while server.auth_code is None and time.time() - start_time < timeout:
            time.sleep(0.1)

        server.shutdown()

        if server.auth_code:
            # Exchange code for access token
            return self._exchange_code_for_token(server.auth_code)
        else:
            raise Exception("Authentication timeout - no authorization code received")

    def _handle_auth_server(self, server):
        """Run the authentication server"""
        server.serve_forever()

    def _exchange_code_for_token(self, code):
        """Exchange authorization code for access token"""
        url = "https://api.clickup.com/api/v2/oauth/token"
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": code,
        }

        response = requests.post(url, data=data)
        if response.status_code == 200:
            token_data = response.json()
            self.access_token = token_data["access_token"]
            self.token_expires_at = time.time() + token_data.get("expires_in", 3600)
            return True
        else:
            raise Exception(
                f"Failed to get access token: {response.status_code} - {response.text}"
            )

    def get_headers(self):
        """Get headers with current access token"""
        if time.time() >= self.token_expires_at:
            # Token expired, need to refresh
            # For simplicity, we'll require re-authentication
            # In production, you'd implement token refresh logic
            raise Exception("Access token expired. Please re-authenticate.")

        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }


class ClickUpTaskManager(QtWidgets.QMainWindow):
    """ClickUp Task Manager for Houdini - OAuth version"""

    def __init__(self, parent=None):
        super(ClickUpTaskManager, self).__init__(parent)
        self.setWindowTitle("ClickUp Task Manager for Houdini (OAuth)")
        self.resize(900, 700)

        # ClickUp API settings
        self.client_id = ""
        self.client_secret = ""
        self.authenticator = None
        self.base_url = "https://api.clickup.com/api/v2"

        # Current workspace/space/list data
        self.current_workspace = None
        self.current_space = None
        self.current_list = None
        self.tasks = []

        # Create the UI
        self.create_ui()

        # Try to load saved credentials
        self.load_credentials()

    def create_ui(self):
        """Create the user interface"""
        central_widget = QtWidgets.QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QtWidgets.QVBoxLayout(central_widget)

        # Authentication Section
        auth_group = QtWidgets.QGroupBox("ClickUp Authentication")
        auth_layout = QtWidgets.QGridLayout()

        client_id_label = QtWidgets.QLabel("Client ID:")
        self.client_id_input = QtWidgets.QLineEdit()
        self.client_id_input.setPlaceholderText("Enter your ClickUp Client ID")

        client_secret_label = QtWidgets.QLabel("Client Secret:")
        self.client_secret_input = QtWidgets.QLineEdit()
        self.client_secret_input.setEchoMode(QtWidgets.QLineEdit.Password)
        self.client_secret_input.setPlaceholderText("Enter your ClickUp Client Secret")

        auth_button = QtWidgets.QPushButton("Authenticate with ClickUp")
        auth_button.clicked.connect(self.authenticate_clickup)

        save_creds_btn = QtWidgets.QPushButton("Save Credentials")
        save_creds_btn.clicked.connect(self.save_credentials)

        auth_layout.addWidget(client_id_label, 0, 0)
        auth_layout.addWidget(self.client_id_input, 0, 1)
        auth_layout.addWidget(client_secret_label, 1, 0)
        auth_layout.addWidget(self.client_secret_input, 1, 1)
        auth_layout.addWidget(auth_button, 2, 0, 1, 2)
        auth_layout.addWidget(save_creds_btn, 3, 0, 1, 2)

        auth_group.setLayout(auth_layout)
        main_layout.addWidget(auth_group)

        # Workspace/Space/List Selection
        selection_group = QtWidgets.QGroupBox("Workspace Selection")
        selection_layout = QtWidgets.QHBoxLayout()

        self.workspace_combo = QtWidgets.QComboBox()
        self.workspace_combo.currentIndexChanged.connect(self.on_workspace_changed)

        self.space_combo = QtWidgets.QComboBox()
        self.space_combo.currentIndexChanged.connect(self.on_space_changed)

        self.list_combo = QtWidgets.QComboBox()
        self.list_combo.currentIndexChanged.connect(self.on_list_changed)

        selection_layout.addWidget(QtWidgets.QLabel("Workspace:"))
        selection_layout.addWidget(self.workspace_combo)
        selection_layout.addWidget(QtWidgets.QLabel("Space:"))
        selection_layout.addWidget(self.space_combo)
        selection_layout.addWidget(QtWidgets.QLabel("List:"))
        selection_layout.addWidget(self.list_combo)

        selection_group.setLayout(selection_layout)
        main_layout.addWidget(selection_group)

        # Task List
        task_group = QtWidgets.QGroupBox("Tasks")
        task_layout = QtWidgets.QVBoxLayout()

        self.task_table = QtWidgets.QTableWidget()
        self.task_table.setColumnCount(5)
        self.task_table.setHorizontalHeaderLabels(
            ["Name", "Status", "Priority", "Due Date", "Assignees"]
        )
        self.task_table.horizontalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.Stretch
        )
        self.task_table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.task_table.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.task_table.cellDoubleClicked.connect(self.on_task_double_clicked)

        task_layout.addWidget(self.task_table)
        task_group.setLayout(task_layout)
        main_layout.addWidget(task_group)

        # Task Actions
        action_layout = QtWidgets.QHBoxLayout()

        create_task_btn = QtWidgets.QPushButton("Create Task")
        create_task_btn.clicked.connect(self.create_task_dialog)

        update_task_btn = QtWidgets.QPushButton("Update Selected")
        update_task_btn.clicked.connect(self.update_task_dialog)

        refresh_btn = QtWidgets.QPushButton("Refresh")
        refresh_btn.clicked.connect(self.refresh_tasks)

        action_layout.addWidget(create_task_btn)
        action_layout.addWidget(update_task_btn)
        action_layout.addWidget(refresh_btn)

        main_layout.addLayout(action_layout)

        # Status bar
        self.status_bar = QtWidgets.QStatusBar()
        self.setStatusBar(self.status_bar)

    def authenticate_clickup(self):
        """Authenticate with ClickUp using OAuth"""
        self.client_id = self.client_id_input.text().strip()
        self.client_secret = self.client_secret_input.text().strip()

        if not self.client_id or not self.client_secret:
            self.status_bar.showMessage("Please enter both Client ID and Client Secret")
            return

        try:
            self.authenticator = ClickUpAuthenticator(
                self.client_id, self.client_secret
            )
            if self.authenticator.authenticate():
                self.status_bar.showMessage("Successfully authenticated with ClickUp!")
                self.load_workspaces()
            else:
                self.status_bar.showMessage("Authentication failed")
        except Exception as e:
            self.status_bar.showMessage(f"Authentication error: {str(e)}")
            QtWidgets.QMessageBox.warning(self, "Authentication Error", str(e))

    def load_workspaces(self):
        """Load workspaces from ClickUp"""
        if not self.authenticator:
            self.status_bar.showMessage("Please authenticate first")
            return

        try:
            headers = self.authenticator.get_headers()
            response = requests.get(f"{self.base_url}/team", headers=headers)

            if response.status_code == 200:
                workspaces = response.json()["teams"]
                self.workspace_combo.clear()

                for workspace in workspaces:
                    self.workspace_combo.addItem(workspace["name"], workspace["id"])

                self.status_bar.showMessage("Workspaces loaded successfully")
            else:
                self.status_bar.showMessage(
                    f"Failed to load workspaces: {response.status_code}"
                )
        except Exception as e:
            self.status_bar.showMessage(f"Error loading workspaces: {str(e)}")

    def save_credentials(self):
        """Save credentials to a file for future use"""
        if not self.client_id_input.text() or not self.client_secret_input.text():
            self.status_bar.showMessage("Please enter credentials before saving")
            return

        creds_data = {
            "client_id": self.client_id_input.text(),
            "client_secret": self.client_secret_input.text(),
        }

        try:
            config_dir = os.path.join(hou.homeHoudiniDirectory(), "config")
            if not os.path.exists(config_dir):
                os.makedirs(config_dir)

            creds_file = os.path.join(config_dir, "clickup_credentials.json")
            with open(creds_file, "w") as f:
                json.dump(creds_data, f)

            self.status_bar.showMessage("Credentials saved successfully")
        except Exception as e:
            self.status_bar.showMessage(f"Error saving credentials: {str(e)}")

    def load_credentials(self):
        """Load saved credentials if they exist"""
        try:
            config_dir = os.path.join(hou.homeHoudiniDirectory(), "config")
            creds_file = os.path.join(config_dir, "clickup_credentials.json")

            if os.path.exists(creds_file):
                with open(creds_file, "r") as f:
                    creds_data = json.load(f)
                    self.client_id_input.setText(creds_data.get("client_id", ""))
                    self.client_secret_input.setText(
                        creds_data.get("client_secret", "")
                    )
                    self.status_bar.showMessage("Credentials loaded from file")
        except Exception as e:
            self.status_bar.showMessage(f"Error loading credentials: {str(e)}")

    # All other methods (on_workspace_changed, load_spaces, etc.) remain the same
    # but replace self.headers with self.authenticator.get_headers()

    def on_workspace_changed(self, index):
        """Handle workspace selection change"""
        if index >= 0:
            workspace_id = self.workspace_combo.itemData(index)
            if workspace_id:
                self.load_spaces(workspace_id)

    def load_spaces(self, workspace_id):
        """Load spaces for the selected workspace"""
        if not self.authenticator:
            return

        try:
            headers = self.authenticator.get_headers()
            response = requests.get(
                f"{self.base_url}/team/{workspace_id}/space", headers=headers
            )
            if response.status_code == 200:
                spaces = response.json()["spaces"]
                self.space_combo.clear()

                for space in spaces:
                    self.space_combo.addItem(space["name"], space["id"])
            else:
                self.status_bar.showMessage(
                    f"Failed to load spaces: {response.status_code}"
                )
        except Exception as e:
            self.status_bar.showMessage(f"Error loading spaces: {str(e)}")

    def on_space_changed(self, index):
        """Handle space selection change"""
        if index >= 0:
            space_id = self.space_combo.itemData(index)
            if space_id:
                self.load_lists(space_id)

    def load_lists(self, space_id):
        """Load lists for the selected space"""
        if not self.authenticator:
            return

        try:
            headers = self.authenticator.get_headers()
            # Add archived=false parameter to only get active lists
            response = requests.get(
                f"{self.base_url}/space/{space_id}/list?archived=false", headers=headers
            )

            if response.status_code == 200:
                data = response.json()
                print(f"Lists API Response: {data}")  # Debug print

                lists = data.get("lists", [])
                self.list_combo.clear()

                if not lists:
                    # Also try loading folders to get nested lists
                    folder_response = requests.get(
                        f"{self.base_url}/space/{space_id}/folder?archived=false",
                        headers=headers,
                    )
                    if folder_response.status_code == 200:
                        folders = folder_response.json().get("folders", [])
                        print(f"Folders API Response: {folders}")  # Debug print

                        # Get lists from each folder
                        for folder in folders:
                            folderless_response = requests.get(
                                f"{self.base_url}/folder/{folder['id']}/list?archived=false",
                                headers=headers,
                            )
                            if folderless_response.status_code == 200:
                                folder_lists = folderless_response.json().get(
                                    "lists", []
                                )
                                for list_item in folder_lists:
                                    self.list_combo.addItem(
                                        f"{folder['name']}/{list_item['name']}",
                                        list_item["id"],
                                    )

                    # Also get folderless lists
                    folderless_response = requests.get(
                        f"{self.base_url}/space/{space_id}/list?archived=false&folder=false",
                        headers=headers,
                    )
                    if folderless_response.status_code == 200:
                        folderless_lists = folderless_response.json().get("lists", [])
                        for list_item in folderless_lists:
                            self.list_combo.addItem(list_item["name"], list_item["id"])
                else:
                    for list_item in lists:
                        self.list_combo.addItem(list_item["name"], list_item["id"])

                if self.list_combo.count() == 0:
                    self.status_bar.showMessage("No lists found in this space")
                else:
                    self.status_bar.showMessage(
                        f"Loaded {self.list_combo.count()} lists"
                    )
            else:
                self.status_bar.showMessage(
                    f"Failed to load lists: {response.status_code} - {response.text}"
                )
                print(f"Error response: {response.text}")  # Debug print
        except Exception as e:
            self.status_bar.showMessage(f"Error loading lists: {str(e)}")
            print(f"Exception loading lists: {str(e)}")  # Debug print

    def on_list_changed(self, index):
        """Handle list selection change"""
        if index >= 0:
            list_id = self.list_combo.itemData(index)
            if list_id:
                self.current_list = list_id
                self.load_tasks(list_id)

    def load_tasks(self, list_id):
        """Load tasks for the selected list"""
        if not self.authenticator:
            return

        try:
            headers = self.authenticator.get_headers()
            # Add parameters to get all tasks including subtasks
            params = {"archived": "false", "include_closed": "true", "subtasks": "true"}

            response = requests.get(
                f"{self.base_url}/list/{list_id}/task", headers=headers, params=params
            )
            print(f"Load tasks response status: {response.status_code}")  # Debug print

            if response.status_code == 200:
                data = response.json()
                print(f"Tasks API Response: {data}")  # Debug print

                self.tasks = data.get("tasks", [])
                self.populate_task_table()

                if not self.tasks:
                    self.status_bar.showMessage("No tasks found in this list")
                else:
                    self.status_bar.showMessage(f"Loaded {len(self.tasks)} tasks")
            else:
                self.status_bar.showMessage(
                    f"Failed to load tasks: {response.status_code} - {response.text}"
                )
                print(f"Error response: {response.text}")  # Debug print
        except Exception as e:
            self.status_bar.showMessage(f"Error loading tasks: {str(e)}")
            print(f"Exception loading tasks: {str(e)}")  # Debug print

    def populate_task_table(self):
        """Populate the task table with current tasks"""
        self.task_table.setRowCount(len(self.tasks))

        for row, task in enumerate(self.tasks):
            # Name
            name_item = QtWidgets.QTableWidgetItem(task.get("name", ""))
            self.task_table.setItem(row, 0, name_item)

            # Status
            status_info = task.get("status", {})
            status_text = (
                status_info.get("status", "Unknown") if status_info else "Unknown"
            )
            status_item = QtWidgets.QTableWidgetItem(status_text)
            self.task_table.setItem(row, 1, status_item)

            # Priority
            priority_info = task.get("priority", None)
            if priority_info:
                # Convert numeric priority to readable string
                priority_val = priority_info.get("priority", None)
                if priority_val == 1:
                    priority_text = "Urgent"
                elif priority_val == 2:
                    priority_text = "High"
                elif priority_val == 3:
                    priority_text = "Normal"
                elif priority_val == 4:
                    priority_text = "Low"
                else:
                    priority_text = "None"
            else:
                priority_text = "None"
            priority_item = QtWidgets.QTableWidgetItem(priority_text)
            self.task_table.setItem(row, 2, priority_item)

            # Due Date
            due_date = task.get("due_date", None)
            if due_date and due_date != "No due date":
                try:
                    due_date_text = datetime.fromtimestamp(
                        int(due_date) / 1000
                    ).strftime("%Y-%m-%d")
                except (ValueError, TypeError):
                    due_date_text = "No due date"
            else:
                due_date_text = "No due date"
            due_date_item = QtWidgets.QTableWidgetItem(due_date_text)
            self.task_table.setItem(row, 3, due_date_item)

            # Assignees
            assignees_list = task.get("assignees", [])
            if assignees_list:
                assignees_text = ", ".join(
                    [
                        assignee.get("username", "")
                        for assignee in assignees_list
                        if assignee
                    ]
                )
            else:
                assignees_text = ""
            assignees_item = QtWidgets.QTableWidgetItem(assignees_text)
            self.task_table.setItem(row, 4, assignees_item)

    def create_task_dialog(self):
        """Show dialog for creating a new task"""
        if not self.authenticator:
            self.status_bar.showMessage("Please authenticate first")
            return

        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle("Create New Task")
        layout = QtWidgets.QVBoxLayout(dialog)

        # Task name
        name_layout = QtWidgets.QHBoxLayout()
        name_label = QtWidgets.QLabel("Task Name:")
        name_input = QtWidgets.QLineEdit()
        name_layout.addWidget(name_label)
        name_layout.addWidget(name_input)
        layout.addLayout(name_layout)

        # Description
        desc_label = QtWidgets.QLabel("Description:")
        desc_input = QtWidgets.QTextEdit()
        layout.addWidget(desc_label)
        layout.addWidget(desc_input)

        # Priority
        priority_layout = QtWidgets.QHBoxLayout()
        priority_label = QtWidgets.QLabel("Priority:")
        priority_combo = QtWidgets.QComboBox()
        priority_combo.addItems(["None", "Low", "Normal", "High", "Urgent"])
        priority_layout.addWidget(priority_label)
        priority_layout.addWidget(priority_combo)
        layout.addLayout(priority_layout)

        # Buttons
        button_layout = QtWidgets.QHBoxLayout()
        create_btn = QtWidgets.QPushButton("Create")
        cancel_btn = QtWidgets.QPushButton("Cancel")
        button_layout.addWidget(create_btn)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)

        create_btn.clicked.connect(
            lambda: self.create_task(
                name_input.text(),
                desc_input.toPlainText(),
                priority_combo.currentText(),
                dialog,
            )
        )
        cancel_btn.clicked.connect(dialog.reject)

        dialog.exec_()

    def update_task_dialog(self):
        """Show dialog for updating the selected task"""
        if not self.authenticator:
            self.status_bar.showMessage("Please authenticate first")
            return

        selected_rows = self.task_table.selectedItems()
        if not selected_rows:
            QtWidgets.QMessageBox.warning(
                self, "Error", "Please select a task to update"
            )
            return

        selected_row = self.task_table.selectedItems()[0].row()
        task = self.tasks[selected_row]

        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle("Update Task")
        layout = QtWidgets.QVBoxLayout(dialog)

        # Status
        status_layout = QtWidgets.QHBoxLayout()
        status_label = QtWidgets.QLabel("Status:")
        status_combo = QtWidgets.QComboBox()

        # Get available statuses for the current list
        list_statuses = self.get_list_statuses()

        for status in list_statuses:
            status_combo.addItem(status["status"], status["status"])

        # Set current status
        current_status = task["status"].get("status", "to do")
        index = status_combo.findData(current_status)
        if index >= 0:
            status_combo.setCurrentIndex(index)

        status_layout.addWidget(status_label)
        status_layout.addWidget(status_combo)
        layout.addLayout(status_layout)

        # Description
        desc_label = QtWidgets.QLabel("Description:")
        desc_input = QtWidgets.QTextEdit()
        desc_input.setText(task.get("description", ""))
        layout.addWidget(desc_label)
        layout.addWidget(desc_input)

        # Assignees
        assignee_layout = QtWidgets.QHBoxLayout()
        assignee_label = QtWidgets.QLabel("Assignee:")
        assignee_combo = QtWidgets.QComboBox()
        assignee_combo.setEnabled(False)  # Will be enabled when members are loaded
        assignee_layout.addWidget(assignee_label)
        assignee_layout.addWidget(assignee_combo)
        layout.addLayout(assignee_layout)

        # Load workspace members and set current assignee
        self.load_workspace_members_for_update(assignee_combo, task)

        # Buttons
        button_layout = QtWidgets.QHBoxLayout()
        update_btn = QtWidgets.QPushButton("Update")
        cancel_btn = QtWidgets.QPushButton("Cancel")
        button_layout.addWidget(update_btn)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)

        update_btn.clicked.connect(
            lambda: self.update_task(
                task["id"],
                status_combo.currentData(),
                desc_input.toPlainText(),
                assignee_combo.currentData(),
                dialog,
            )
        )
        cancel_btn.clicked.connect(dialog.reject)

        dialog.exec_()

    def get_list_statuses(self):
        """Get available statuses for the current list"""
        if not self.current_list or not self.authenticator:
            return [
                {"status": "to do"},
                {"status": "in progress"},
                {"status": "completed"},
            ]

        try:
            headers = self.authenticator.get_headers()
            response = requests.get(
                f"{self.base_url}/list/{self.current_list}", headers=headers
            )

            if response.status_code == 200:
                list_data = response.json()
                statuses = list_data.get("statuses", [])
                return statuses
            else:
                print(f"Failed to get list statuses: {response.status_code}")
                print(f"Response: {response.text}")
                return [
                    {"status": "to do"},
                    {"status": "in progress"},
                    {"status": "completed"},
                ]
        except Exception as e:
            print(f"Error getting list statuses: {str(e)}")
            return [
                {"status": "to do"},
                {"status": "in progress"},
                {"status": "completed"},
            ]

    def load_workspace_members_for_update(self, assignee_combo, task):
        """Load workspace members for assignee selection in update dialog"""
        workspace_id = self.workspace_combo.currentData()
        if not workspace_id or not self.authenticator:
            return

        try:
            headers = self.authenticator.get_headers()
            # First get task members for the specific list
            response = requests.get(
                f"{self.base_url}/list/{self.current_list}/member", headers=headers
            )

            if response.status_code == 200:
                members = response.json().get("members", [])

                assignee_combo.clear()
                assignee_combo.addItem("Unassigned", None)

                current_assignee_id = None
                if task.get("assignees"):
                    current_assignee_id = task["assignees"][0].get("id")

                for member in members:
                    username = member.get("username", member.get("email", "Unknown"))
                    user_id = member.get("id")
                    if user_id:
                        assignee_combo.addItem(username, user_id)

                        # Set current assignee if it matches
                        if user_id == current_assignee_id:
                            assignee_combo.setCurrentIndex(assignee_combo.count() - 1)

                # If current assignee not found in list members, try workspace members
                if current_assignee_id and assignee_combo.currentIndex() == 0:
                    workspace_response = requests.get(
                        f"{self.base_url}/team/{workspace_id}", headers=headers
                    )
                    if workspace_response.status_code == 200:
                        team_data = workspace_response.json()
                        team_members = team_data.get("team", {}).get("members", [])

                        for member in team_members:
                            user = member.get("user", {})
                            username = user.get(
                                "username", user.get("email", "Unknown")
                            )
                            user_id = user.get("id")
                            if user_id and user_id not in [
                                assignee_combo.itemData(i)
                                for i in range(assignee_combo.count())
                            ]:
                                assignee_combo.addItem(username, user_id)

                                # Set current assignee if it matches
                                if user_id == current_assignee_id:
                                    assignee_combo.setCurrentIndex(
                                        assignee_combo.count() - 1
                                    )

                assignee_combo.setEnabled(True)
            else:
                print(f"Failed to load workspace members: {response.status_code}")
                print(f"Response: {response.text}")
        except Exception as e:
            print(f"Error loading workspace members: {str(e)}")
            import traceback

            traceback.print_exc()

    def update_task(self, task_id, status, description, assignee_id, dialog):
        """Update a task in ClickUp"""
        if not self.authenticator:
            return

        update_data = {"status": status, "description": description}

        # Update assignees separately if changed
        if assignee_id != "current":  # "current" means no change
            if assignee_id:
                # Add assignee
                update_data["assignees"] = {"add": [assignee_id]}
            else:
                # Get current assignees to remove them all
                current_task = None
                for task in self.tasks:
                    if task["id"] == task_id:
                        current_task = task
                        break

                if current_task and current_task.get("assignees"):
                    # Remove all current assignees
                    current_assignee_ids = [
                        a.get("id") for a in current_task["assignees"] if a.get("id")
                    ]
                    if current_assignee_ids:
                        update_data["assignees"] = {"rem": current_assignee_ids}

        try:
            headers = self.authenticator.get_headers()
            print(f"Updating task {task_id} with data: {update_data}")  # Debug print

            response = requests.put(
                f"{self.base_url}/task/{task_id}", headers=headers, json=update_data
            )

            print(f"Update task response status: {response.status_code}")  # Debug print
            print(f"Update task response: {response.text}")  # Debug print

            if response.status_code == 200:
                self.status_bar.showMessage("Task updated successfully")
                dialog.accept()
                self.refresh_tasks()
            else:
                error_message = f"Failed to update task: {response.status_code}"
                if response.text:
                    try:
                        error_data = response.json()
                        error_message += f"\n{error_data.get('err', error_data)}"
                    except Exception:
                        error_message += f"\n{response.text}"
                QtWidgets.QMessageBox.warning(self, "Error", error_message)
        except Exception as e:
            QtWidgets.QMessageBox.warning(
                self, "Error", f"Error updating task: {str(e)}"
            )
            print(f"Exception updating task: {str(e)}")  # Debug print

    def create_task(self, name, description, priority, dialog):
        """Create a new task in ClickUp"""
        if not name:
            QtWidgets.QMessageBox.warning(self, "Error", "Task name is required")
            return

        if not self.authenticator:
            QtWidgets.QMessageBox.warning(self, "Error", "Not authenticated")
            return

        if not self.current_list:
            QtWidgets.QMessageBox.warning(self, "Error", "No list selected")
            return

        # Convert priority to ClickUp format
        priority_map = {"None": None, "Low": 4, "Normal": 3, "High": 2, "Urgent": 1}

        task_data = {
            "name": name,
            "description": description,
            # Use "to do" instead of "Open" based on your existing tasks
            "status": "to do",
        }

        # Add priority only if it's not None
        if priority_map.get(priority) is not None:
            task_data["priority"] = priority_map.get(priority)

        try:
            headers = self.authenticator.get_headers()
            print(f"Creating task in list: {self.current_list}")  # Debug print
            print(f"Task data: {task_data}")  # Debug print

            response = requests.post(
                f"{self.base_url}/list/{self.current_list}/task",
                headers=headers,
                json=task_data,
            )

            print(f"Create task response status: {response.status_code}")  # Debug print
            print(f"Create task response: {response.text}")  # Debug print

            if response.status_code == 200:
                self.status_bar.showMessage("Task created successfully")
                dialog.accept()
                self.refresh_tasks()
            else:
                error_message = f"Failed to create task: {response.status_code}"
                if response.text:
                    try:
                        error_data = response.json()
                        error_message += f"\n{error_data.get('err', error_data)}"
                    except Exception:
                        error_message += f"\n{response.text}"
                QtWidgets.QMessageBox.warning(self, "Error", error_message)
        except Exception as e:
            QtWidgets.QMessageBox.warning(
                self, "Error", f"Error creating task: {str(e)}"
            )
            print(f"Exception creating task: {str(e)}")  # Debug print

    def create_audit_log(self):
        """Create an audit log entry for current tasks"""
        if not self.current_list:
            QtWidgets.QMessageBox.warning(self, "Error", "Please select a list first")
            return

        if not self.authenticator:
            self.status_bar.showMessage("Please authenticate first")
            return

        workspace_id = self.workspace_combo.currentData()
        if not workspace_id:
            QtWidgets.QMessageBox.warning(
                self, "Error", "Please select a workspace first"
            )
            return

        # Create audit log entry with current tasks
        task_summary = []
        for task in self.tasks:
            task_summary.append(f"{task['name']} - {task['status']['status']}")

        audit_data = {
            "workspace_id": workspace_id,
            "location": 29,  # Custom location type as per API
            "action": "Task Summary from Houdini",
            "entity_id": str(self.current_list),
            "entity_type": "list",
            "metadata": {
                "task_count": len(self.tasks),
                "tasks": task_summary,
                "timestamp": datetime.now().isoformat(),
                "source": "Houdini Task Manager",
            },
        }

        try:
            headers = self.authenticator.get_headers()
            print(f"Creating audit log with data: {audit_data}")  # Debug print

            response = requests.post(
                f"{self.base_url}/workspaces/{workspace_id}/audit_logs",
                headers=headers,
                json=audit_data,
            )

            print(f"Audit log response status: {response.status_code}")  # Debug print
            print(f"Audit log response: {response.text}")  # Debug print

            if response.status_code == 200:
                self.status_bar.showMessage("Audit log created successfully")
            else:
                error_message = f"Failed to create audit log: {response.status_code}"
                if response.text:
                    try:
                        error_data = response.json()
                        error_message += f"\n{error_data.get('error', error_data.get('err', 'Unknown error'))}"
                    except Exception:
                        error_message += f"\n{response.text}"
                QtWidgets.QMessageBox.warning(self, "Error", error_message)
        except Exception as e:
            QtWidgets.QMessageBox.warning(
                self, "Error", f"Error creating audit log: {str(e)}"
            )
            print(f"Exception creating audit log: {str(e)}")  # Debug print

    def refresh_tasks(self):
        """Refresh the current task list"""
        if self.current_list:
            self.load_tasks(self.current_list)

    def on_task_double_clicked(self, row, column):
        """Handle double-click on a task"""
        task = self.tasks[row]
        # Create a Houdini node with task information
        self.create_houdini_task_node(task)

    def create_houdini_task_node(self, task):
        """Create a Houdini node to represent the task"""
        # Create a null node in /obj context
        obj_node = hou.node("/obj")
        task_node = obj_node.createNode(
            "null", f"TASK_{task['name'][:20].replace(' ', '_')}"
        )

        # Add parameters to store task information
        parm_template_group = task_node.parmTemplateGroup()

        # Task ID
        task_id_parm = hou.StringParmTemplate("task_id", "Task ID", 1)
        task_id_parm.setDefaultValue((task["id"],))
        parm_template_group.append(task_id_parm)

        # Task Name
        task_name_parm = hou.StringParmTemplate("task_name", "Task Name", 1)
        task_name_parm.setDefaultValue((task["name"],))
        parm_template_group.append(task_name_parm)

        # Status
        status_parm = hou.StringParmTemplate("status", "Status", 1)
        status_parm.setDefaultValue((task["status"]["status"],))
        parm_template_group.append(status_parm)

        # Description
        if "description" in task:
            desc_parm = hou.StringParmTemplate(
                "description", "Description", 1, num_components=1
            )
            desc_parm.setDefaultValue((task["description"],))
            parm_template_group.append(desc_parm)

        task_node.setParmTemplateGroup(parm_template_group)

        # Set node color based on status
        status_colors = {
            "Open": hou.Color((1, 0.5, 0.5)),  # Red
            "In Progress": hou.Color((1, 1, 0.5)),  # Yellow
            "Review": hou.Color((0.5, 0.5, 1)),  # Blue
            "Completed": hou.Color((0.5, 1, 0.5)),  # Green
        }
        task_node.setColor(
            status_colors.get(task["status"]["status"], hou.Color((0.5, 0.5, 0.5)))
        )

        # Select the node
        task_node.setSelected(True, clear_all_selected=True)

        self.status_bar.showMessage(f"Created Houdini node for task: {task['name']}")


# Function to launch the tool
def show_clickup_task_manager():
    """Launch the ClickUp Task Manager"""
    task_manager = ClickUpTaskManager(hou.ui.mainQtWindow())
    task_manager.show()
    return task_manager


# Store instance to prevent garbage collection
_task_manager_instance = None


def launch_task_manager():
    """Show the task manager tool (creates a new instance if needed)"""
    global _task_manager_instance

    if _task_manager_instance and not _task_manager_instance.isVisible():
        _task_manager_instance.show()
        _task_manager_instance.raise_()
        _task_manager_instance.activateWindow()
    else:
        _task_manager_instance = show_clickup_task_manager()

    return _task_manager_instance


class PomodoroDialog(QtWidgets.QDialog):
    """Pomodoro Timer Dialog with Time Tracking"""

    def __init__(self, task_manager, parent=None):
        super(PomodoroDialog, self).__init__(parent)
        self.task_manager = task_manager
        self.setWindowTitle("Pomodoro Timer")
        self.resize(400, 300)

        # Timer variables
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_timer)
        self.time_remaining = 0
        self.session_duration = 0
        self.is_running = False
        self.current_task_id = None

        # Create UI
        self.create_ui()

        # Load tasks from task manager
        self.load_tasks()

    def create_ui(self):
        """Create the user interface"""
        layout = QtWidgets.QVBoxLayout(self)

        # Task selection
        task_layout = QtWidgets.QHBoxLayout()
        task_label = QtWidgets.QLabel("Task:")
        self.task_combo = QtWidgets.QComboBox()
        self.task_combo.setMinimumWidth(250)
        task_layout.addWidget(task_label)
        task_layout.addWidget(self.task_combo)
        layout.addLayout(task_layout)

        # Time selection
        time_layout = QtWidgets.QHBoxLayout()
        time_label = QtWidgets.QLabel("Duration:")
        self.time_combo = QtWidgets.QComboBox()

        # Add time options in 15-minute intervals up to 2 hours
        for minutes in range(15, 121, 15):
            hours = minutes // 60
            remaining_minutes = minutes % 60
            if hours > 0:
                display_text = (
                    f"{hours}h {remaining_minutes}m"
                    if remaining_minutes > 0
                    else f"{hours}h"
                )
            else:
                display_text = f"{minutes}m"
            self.time_combo.addItem(display_text, minutes)

        # Set default to 25 minutes (Pomodoro standard)
        index = self.time_combo.findData(25)
        if index >= 0:
            self.time_combo.setCurrentIndex(index)

        time_layout.addWidget(time_label)
        time_layout.addWidget(self.time_combo)
        layout.addLayout(time_layout)

        # Timer display
        self.timer_display = QtWidgets.QLabel("00:00")
        self.timer_display.setAlignment(QtCore.Qt.AlignCenter)
        self.timer_display.setStyleSheet(
            """
            QLabel {
                font-size: 48px;
                font-weight: bold;
                color: white;
                background-color: #333333;
                border-radius: 10px;
                padding: 20px;
            }
        """
        )
        layout.addWidget(self.timer_display)

        # Control buttons
        button_layout = QtWidgets.QHBoxLayout()
        self.start_button = QtWidgets.QPushButton("Start")
        self.start_button.clicked.connect(self.start_timer)
        self.pause_button = QtWidgets.QPushButton("Pause")
        self.pause_button.clicked.connect(self.pause_timer)
        self.pause_button.setEnabled(False)
        self.reset_button = QtWidgets.QPushButton("Reset")
        self.reset_button.clicked.connect(self.reset_timer)
        self.reset_button.setEnabled(False)

        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.pause_button)
        button_layout.addWidget(self.reset_button)
        layout.addLayout(button_layout)

        # Status label
        self.status_label = QtWidgets.QLabel("")
        self.status_label.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(self.status_label)

        # Refresh tasks button
        refresh_button = QtWidgets.QPushButton("Refresh Tasks")
        refresh_button.clicked.connect(self.load_tasks)
        layout.addWidget(refresh_button)

    def load_tasks(self):
        """Load tasks from the task manager"""
        self.task_combo.clear()

        if not self.task_manager.current_list:
            self.status_label.setText("Please select a list in the Task Manager first")
            return

        if not self.task_manager.tasks:
            self.status_label.setText("No tasks found")
            return

        for task in self.task_manager.tasks:
            task_name = task.get("name", "Unnamed Task")
            task_id = task.get("id", "")
            if task_id:
                self.task_combo.addItem(task_name, task_id)

        self.status_label.setText(f"Loaded {len(self.task_manager.tasks)} tasks")

    def start_timer(self):
        """Start the timer"""
        if not self.task_combo.currentData():
            self.status_label.setText("Please select a task first")
            return

        if not self.is_running:
            selected_minutes = self.time_combo.currentData()
            self.session_duration = selected_minutes * 60  # Convert to seconds
            self.time_remaining = self.session_duration
            self.current_task_id = self.task_combo.currentData()

            self.timer.start(1000)  # Update every second
            self.is_running = True

            self.start_button.setEnabled(False)
            self.pause_button.setEnabled(True)
            self.reset_button.setEnabled(True)
            self.task_combo.setEnabled(False)
            self.time_combo.setEnabled(False)

            self.status_label.setText("Timer running...")

    def pause_timer(self):
        """Pause the timer"""
        if self.is_running:
            self.timer.stop()
            self.is_running = False
            self.start_button.setEnabled(True)
            self.pause_button.setEnabled(False)
            self.status_label.setText("Timer paused")

    def reset_timer(self):
        """Reset the timer"""
        self.timer.stop()
        self.is_running = False
        self.time_remaining = 0

        self.start_button.setEnabled(True)
        self.pause_button.setEnabled(False)
        self.reset_button.setEnabled(False)
        self.task_combo.setEnabled(True)
        self.time_combo.setEnabled(True)

        self.timer_display.setText("00:00")
        self.status_label.setText("Timer reset")

    def update_timer(self):
        """Update the timer display"""
        if self.time_remaining > 0:
            self.time_remaining -= 1
            minutes = self.time_remaining // 60
            seconds = self.time_remaining % 60
            self.timer_display.setText(f"{minutes:02d}:{seconds:02d}")
        else:
            self.timer.stop()
            self.is_running = False
            self.timer_display.setText("00:00")
            self.on_timer_complete()

    def on_timer_complete(self):
        """Handle timer completion"""
        self.status_label.setText("Session complete! Updating time tracking...")

        # Update time tracking in ClickUp
        if self.current_task_id:
            success = self.update_time_tracking(
                self.current_task_id, self.session_duration
            )

            if success:
                QtWidgets.QMessageBox.information(
                    self,
                    "Timer Complete",
                    f"Session complete! Added {self.time_combo.currentText()} to task time tracking.",
                )
            else:
                QtWidgets.QMessageBox.warning(
                    self,
                    "Update Failed",
                    "Session complete, but failed to update time tracking in ClickUp.",
                )

        # Reset timer UI
        self.reset_timer()

    def update_time_tracking(self, task_id, duration_seconds):
        """Update time tracking for a task in ClickUp"""
        if not self.task_manager.authenticator:
            self.status_label.setText("Not authenticated with ClickUp")
            return False

        try:
            headers = self.task_manager.authenticator.get_headers()

            # Get current time tracking data
            response = requests.get(
                f"{self.task_manager.base_url}/task/{task_id}",
                headers=headers,
                params={"custom_fields": "true"},
            )

            if response.status_code != 200:
                print(f"Failed to get task data: {response.status_code}")
                return False

            # task_data = response.json()

            # Calculate new time in milliseconds
            duration_ms = duration_seconds * 1000

            # Create time entry
            time_entry_data = {
                "description": "Pomodoro session from Houdini",
                "start": int(
                    (datetime.now() - timedelta(seconds=duration_seconds)).timestamp()
                    * 1000
                ),
                "end": int(datetime.now().timestamp() * 1000),
                "duration": duration_ms,
            }

            # Post time entry
            entry_response = requests.post(
                f"{self.task_manager.base_url}/task/{task_id}/time_entry",
                headers=headers,
                json=time_entry_data,
            )

            if entry_response.status_code == 200:
                self.status_label.setText("Time tracking updated successfully")
                # Refresh task manager display
                self.task_manager.refresh_tasks()
                return True
            else:
                print(f"Failed to create time entry: {entry_response.status_code}")
                print(f"Response: {entry_response.text}")
                self.status_label.setText("Failed to update time tracking")
                return False

        except Exception as e:
            print(f"Error updating time tracking: {str(e)}")
            self.status_label.setText(f"Error: {str(e)}")
            return False


# Update the ClickUpTaskManager class to add the Pomodoro timer button
def extend_clickup_task_manager():
    """Extend the ClickUpTaskManager class with Pomodoro timer functionality"""

    original_create_ui = ClickUpTaskManager.create_ui

    def new_create_ui(self):
        """Extended create_ui method with Pomodoro timer button"""
        # Call the original create_ui method
        original_create_ui(self)

        # Find the action layout in the main layout
        main_layout = self.centralWidget().layout()
        action_layout = None

        # Find the action layout
        for i in range(main_layout.count()):
            item = main_layout.itemAt(i)
            if isinstance(item, QtWidgets.QHBoxLayout):
                layout = item
                # Check if this layout contains the refresh button
                for j in range(layout.count()):
                    widget = layout.itemAt(j).widget()
                    if (
                        widget
                        and isinstance(widget, QtWidgets.QPushButton)
                        and widget.text() == "Refresh"
                    ):
                        action_layout = layout
                        break
                if action_layout:
                    break

        if action_layout:
            # Add Pomodoro timer button
            pomodoro_btn = QtWidgets.QPushButton("Pomodoro Timer")
            pomodoro_btn.clicked.connect(partial(show_pomodoro_timer, self))
            action_layout.addWidget(pomodoro_btn)

    # Replace the create_ui method
    ClickUpTaskManager.create_ui = new_create_ui


def show_pomodoro_timer(task_manager):
    """Show the Pomodoro timer dialog"""
    dialog = PomodoroDialog(task_manager, task_manager)
    dialog.exec_()


# Apply the extension to the ClickUpTaskManager class
extend_clickup_task_manager()


# Optional: If you want to create a standalone Pomodoro timer button in your shelf
def launch_pomodoro_timer():
    """Launch the Pomodoro timer directly"""
    # Try to find existing task manager instance
    task_manager = None
    for widget in QtWidgets.QApplication.topLevelWidgets():
        if isinstance(widget, ClickUpTaskManager) and widget.isVisible():
            task_manager = widget
            break

    if task_manager:
        show_pomodoro_timer(task_manager)
    else:
        # Create a new task manager instance
        task_manager = ClickUpTaskManager(hou.ui.mainQtWindow())
        task_manager.show()
        # Show Pomodoro timer after the task manager is visible
        QtCore.QTimer.singleShot(100, lambda: show_pomodoro_timer(task_manager))
