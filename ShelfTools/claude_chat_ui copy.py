"""
Claude Chat UI for Houdini
-------------------------
A chat interface for communicating with Claude AI directly within Houdini.
"""

import hou
import os
import json
import sys
import anthropic  # ADD THIS IMPORT
from PySide2 import QtCore, QtWidgets, QtGui


class ClaudeChatUI(QtWidgets.QMainWindow):
    """Main chat window for Claude AI interaction"""
    
    def __init__(self, parent=None):
        super(ClaudeChatUI, self).__init__(parent)
        self.setWindowTitle("Claude AI Assistant")
        self.resize(800, 600)
        self.setWindowFlags(QtCore.Qt.Window)
        
        # Initialize chat history
        self.chat_history = []
        
        # API key placeholder - you'll need to replace this
        self.api_key = None
        
        # Create central widget
        self.central_widget = QtWidgets.QWidget()
        self.setCentralWidget(self.central_widget)
        
        # Create the UI
        self.create_ui()
        
        # Load API key from environment or file
        self.load_api_key()
    
    def create_ui(self):
        """Create the chat interface"""
        main_layout = QtWidgets.QVBoxLayout(self.central_widget)
        
        # Create toolbar
        toolbar = QtWidgets.QHBoxLayout()
        
        # API Key configuration button
        self.api_key_button = QtWidgets.QPushButton("Configure API Key")
        self.api_key_button.clicked.connect(self.configure_api_key)
        
        # Clear chat button
        self.clear_button = QtWidgets.QPushButton("Clear Chat")
        self.clear_button.clicked.connect(self.clear_chat)
        
        toolbar.addWidget(self.api_key_button)
        toolbar.addWidget(self.clear_button)
        toolbar.addStretch()
        
        main_layout.addLayout(toolbar)
        
        # Create chat display area
        self.chat_display = QtWidgets.QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setStyleSheet("""
            QTextEdit {
                background-color: #1E1E1E;
                color: #FFFFFF;
                font-family: Consolas, Monaco, monospace;
                font-size: 14px;
                padding: 10px;
                border: 1px solid #333333;
            }
        """)
        
        main_layout.addWidget(self.chat_display)
        
        # Create input area
        input_layout = QtWidgets.QHBoxLayout()
        
        self.input_field = QtWidgets.QTextEdit()
        self.input_field.setMaximumHeight(100)
        self.input_field.setPlaceholderText("Type your message here... (Ctrl+Enter to send)")
        self.input_field.setStyleSheet("""
            QTextEdit {
                background-color: #2A2A2A;
                color: #FFFFFF;
                font-family: Consolas, Monaco, monospace;
                font-size: 14px;
                padding: 5px;
                border: 1px solid #444444;
            }
        """)
        
        # Install event filter to handle Ctrl+Enter
        self.input_field.installEventFilter(self)
        
        self.send_button = QtWidgets.QPushButton("Send")
        self.send_button.setFixedWidth(80)
        self.send_button.clicked.connect(self.send_message)
        self.send_button.setStyleSheet("""
            QPushButton {
                background-color: #0078D4;
                color: white;
                border: none;
                padding: 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #006CBE;
            }
            QPushButton:pressed {
                background-color: #0062A3;
            }
        """)
        
        input_layout.addWidget(self.input_field)
        input_layout.addWidget(self.send_button)
        
        main_layout.addLayout(input_layout)
        
        # Status bar
        self.status_bar = QtWidgets.QStatusBar()
        self.setStatusBar(self.status_bar)
    
    def eventFilter(self, obj, event):
        """Handle Ctrl+Enter shortcut"""
        if obj == self.input_field and event.type() == QtCore.QEvent.KeyPress:
            if event.key() == QtCore.Qt.Key_Return and event.modifiers() == QtCore.Qt.ControlModifier:
                self.send_message()
                return True
        return super().eventFilter(obj, event)
    
    def load_api_key(self):
        """Load API key from environment or configuration file"""
        # First check environment variable
        api_key = os.environ.get('ANTHROPIC_API_KEY')
        
        if not api_key:
            # Check config file
            config_path = os.path.join(hou.homeHoudiniDirectory(), 'claude_config.json')
            if os.path.exists(config_path):
                try:
                    with open(config_path, 'r') as f:
                        config = json.load(f)
                        api_key = config.get('api_key')
                except Exception as e:
                    print(f"Error loading config: {e}")
        
        if api_key:
            self.api_key = api_key
            self.status_bar.showMessage("API key loaded successfully")
        else:
            self.status_bar.showMessage("No API key found - please configure")
    
    def configure_api_key(self):
        """Show dialog to configure API key"""
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle("Configure API Key")
        dialog.resize(400, 120)
        
        layout = QtWidgets.QVBoxLayout(dialog)
        
        # Information label
        info_label = QtWidgets.QLabel(
            "Enter your Anthropic API key. This will be saved securely in your Houdini config folder."
        )
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # API key input
        key_layout = QtWidgets.QHBoxLayout()
        key_label = QtWidgets.QLabel("API Key:")
        key_input = QtWidgets.QLineEdit()
        key_input.setEchoMode(QtWidgets.QLineEdit.Password)
        key_input.setText(self.api_key or "")
        
        key_layout.addWidget(key_label)
        key_layout.addWidget(key_input)
        layout.addLayout(key_layout)
        
        # Buttons
        button_layout = QtWidgets.QHBoxLayout()
        save_button = QtWidgets.QPushButton("Save")
        cancel_button = QtWidgets.QPushButton("Cancel")
        
        button_layout.addWidget(save_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)
        
        # Connect signals
        save_button.clicked.connect(lambda: self.save_api_key(key_input.text(), dialog))
        cancel_button.clicked.connect(dialog.reject)
        
        dialog.exec_()
    
    def save_api_key(self, api_key, dialog):
        """Save API key to configuration file"""
        if not api_key:
            QtWidgets.QMessageBox.warning(self, "Error", "API key cannot be empty")
            return
        
        config_path = os.path.join(hou.homeHoudiniDirectory(), 'claude_config.json')
        config = {'api_key': api_key}
        
        try:
            with open(config_path, 'w') as f:
                json.dump(config, f)
            
            self.api_key = api_key
            self.status_bar.showMessage("API key saved successfully")
            dialog.accept()
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", f"Failed to save API key: {e}")
    
    def clear_chat(self):
        """Clear the chat history"""
        self.chat_history = []
        self.chat_display.clear()
        self.status_bar.showMessage("Chat cleared")
    
    def send_message(self):
        """Send message to Claude API"""
        message = self.input_field.toPlainText().strip()
        if not message:
            return
        
        if not self.api_key:
            QtWidgets.QMessageBox.warning(
                self, 
                "API Key Required", 
                "Please configure your API key first"
            )
            return
        
        # Clear the input field
        self.input_field.clear()
        
        # Add user message to chat display
        self.append_message("You", message, "#0078D4")
        
        # Send to Claude API
        self.status_bar.showMessage("Sending message to Claude...")
        
        # Call the receive_response method (not simulate_response)
        QtCore.QTimer.singleShot(100, lambda: self.receive_response(message))
    
    def send_to_claude(self, message):
        """Send message to Claude API and get response"""
        try:
            client = anthropic.Anthropic(api_key=self.api_key)
            
            # Build conversation history for context
            messages = []
            for msg in self.chat_history:
                messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
            
            # Add current message
            messages.append({
                "role": "user",
                "content": message
            })
            
            # Send to Claude API
            response = client.messages.create(
                model="claude-3-7-sonnet-20250219",
                max_tokens=1000,
                messages=messages
            )
            
            # Get response text
            response_text = response.content[0].text
            
            # Add to chat history
            self.chat_history.append({"role": "user", "content": message})
            self.chat_history.append({"role": "assistant", "content": response_text})
            
            return response_text
            
        except Exception as e:
            self.status_bar.showMessage(f"Error: {str(e)}")
            return f"Error: {str(e)}"
    
    def receive_response(self, message):
        """Receive response from Claude API"""
        response = self.send_to_claude(message)
        self.append_message("Claude", response, "#00A36C")
        self.status_bar.showMessage("Response received")
    
    def append_message(self, sender, message, color):
        """Append a message to the chat display"""
        timestamp = QtCore.QDateTime.currentDateTime().toString("hh:mm:ss")
        
        formatted_message = f"""
<div style="margin: 10px 0;">
    <div style="color: {color}; font-weight: bold;">{sender} [{timestamp}]</div>
    <div style="color: #FFFFFF; white-space: pre-wrap;">{message}</div>
</div>
<hr style="border: 1px solid #333333;">
"""
        
        # Move cursor to end before inserting
        cursor = self.chat_display.textCursor()
        cursor.movePosition(QtGui.QTextCursor.End)
        self.chat_display.setTextCursor(cursor)
        
        # Insert HTML
        self.chat_display.insertHtml(formatted_message)
        
        # Scroll to bottom
        self.chat_display.verticalScrollBar().setValue(
            self.chat_display.verticalScrollBar().maximum()
        )


def show_claude_chat():
    """Show the Claude chat interface"""
    global _chat_instance
    
    try:
        if _chat_instance.isVisible():
            _chat_instance.raise_()
            _chat_instance.activateWindow()
        else:
            _chat_instance.show()
    except:
        _chat_instance = ClaudeChatUI(hou.ui.mainQtWindow())
        _chat_instance.show()
    
    return _chat_instance


# Global instance to prevent garbage collection
_chat_instance = None


# Entry point for standalone use
if __name__ == "__main__":
    show_claude_chat()