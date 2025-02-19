# SettingsDialog.py

from PyQt5.QtWidgets import QDialog, QVBoxLayout, QRadioButton, QButtonGroup, QFormLayout, QLineEdit, QPushButton, QDialogButtonBox
from PyQt5.QtCore import Qt
import os


class SettingsDialog(QDialog):
    """
    A settings dialog for switching between Ollama, OpenAI, and Azure OpenAI
    and adjusting host/keys.
    """
    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self.settings = settings
        self.setWindowTitle("Geominds - Settings")
        self.setMinimumSize(600, 400)  # Adjusted size

        layout = QVBoxLayout()

        # API Type Selection
        self.api_group = QButtonGroup(self)
        self.ollama_radio = QRadioButton("Ollama")
        self.openai_radio = QRadioButton("OpenAI")
        self.azure_openai_radio = QRadioButton("Azure OpenAI")
        self.api_group.addButton(self.ollama_radio)
        self.api_group.addButton(self.openai_radio)
        self.api_group.addButton(self.azure_openai_radio)
        layout.addWidget(self.ollama_radio)
        layout.addWidget(self.openai_radio)
        layout.addWidget(self.azure_openai_radio)

        # Form fields
        self.form_layout = QFormLayout()
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QRadioButton, QButtonGroup, 
    QFormLayout, QLineEdit, QPushButton, QDialogButtonBox, QWidget, QTabWidget,
    QComboBox, QCheckBox, QSpinBox, QLabel, QGroupBox)
from PyQt5.QtCore import Qt
import os

class SettingsDialog(QDialog):
    """
    An improved settings dialog with tabbed interface and dynamic API settings.
    """
    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self.settings = settings
        self.setWindowTitle("Geominds - Settings")
        self.setMinimumSize(500, 400)

        # Main layout
        layout = QVBoxLayout()
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        
        # Create tabs
        self.api_tab = QWidget()
        self.error_tab = QWidget()
        
        self.setup_api_tab()
        self.setup_error_tab()
        
        self.tab_widget.addTab(self.api_tab, "API Settings")
        self.tab_widget.addTab(self.error_tab, "Error Handling")
        
        layout.addWidget(self.tab_widget)

        # OK/Cancel Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        self.setLayout(layout)
        self.load_from_settings()

    def setup_api_tab(self):
        """Setup the API settings tab with dynamic field visibility."""
        layout = QVBoxLayout()

        # API Type Selection
        api_group = QGroupBox("API Type")
        api_layout = QVBoxLayout()
        
        self.api_group = QButtonGroup(self)
        self.ollama_radio = QRadioButton("Ollama")
        self.openai_radio = QRadioButton("OpenAI")
        self.azure_openai_radio = QRadioButton("Azure OpenAI")
        
        for radio in [self.ollama_radio, self.openai_radio, self.azure_openai_radio]:
            self.api_group.addButton(radio)
            api_layout.addWidget(radio)
        
        api_group.setLayout(api_layout)
        layout.addWidget(api_group)

        # Create containers for each API's settings
        self.ollama_container = QWidget()
        self.openai_container = QWidget()
        self.azure_container = QWidget()

        # Ollama Settings
        ollama_layout = QFormLayout()
        self.ollama_host_input = QLineEdit()
        self.ollama_model_input = QLineEdit()
        ollama_layout.addRow("Host:", self.ollama_host_input)
        ollama_layout.addRow("Model:", self.ollama_model_input)
        self.ollama_container.setLayout(ollama_layout)

        # OpenAI Settings
        openai_layout = QFormLayout()
        self.openai_url_input = QLineEdit()
        self.openai_key_input = QLineEdit()
        self.openai_key_input.setEchoMode(QLineEdit.Password)
        self.openai_model_input = QLineEdit()
        openai_layout.addRow("API URL:", self.openai_url_input)
        openai_layout.addRow("API Key:", self.openai_key_input)
        openai_layout.addRow("Model:", self.openai_model_input)
        self.openai_container.setLayout(openai_layout)

        # Azure OpenAI Settings
        azure_layout = QFormLayout()
        self.azure_endpoint_input = QLineEdit()
        self.azure_deployment_input = QLineEdit()
        self.azure_api_version_input = QLineEdit()
        self.azure_api_key_input = QLineEdit()
        self.azure_api_key_input.setEchoMode(QLineEdit.Password)
        azure_layout.addRow("Endpoint URL:", self.azure_endpoint_input)
        azure_layout.addRow("Deployment Name:", self.azure_deployment_input)
        azure_layout.addRow("API Version:", self.azure_api_version_input)
        azure_layout.addRow("API Key:", self.azure_api_key_input)
        self.azure_container.setLayout(azure_layout)

        # Add containers to main layout
        layout.addWidget(self.ollama_container)
        layout.addWidget(self.openai_container)
        layout.addWidget(self.azure_container)
        
        # Add stretch to push everything to the top
        layout.addStretch()
        
        self.api_tab.setLayout(layout)

        # Connect radio buttons to visibility toggle
        self.ollama_radio.toggled.connect(self.toggle_containers)
        self.openai_radio.toggled.connect(self.toggle_containers)
        self.azure_openai_radio.toggled.connect(self.toggle_containers)

    # In your SettingsDialog class
    def setup_error_tab(self):
        """Setup the error handling settings tab."""
        layout = QFormLayout()

        # Error Sensitivity
        self.error_sensitivity = QComboBox()
        self.error_sensitivity.addItems(["low", "medium", "high"])
        layout.addRow("Error Sensitivity:", self.error_sensitivity)

        # Auto Intercept
        self.auto_intercept = QCheckBox()
        layout.addRow("Auto Intercept:", self.auto_intercept)

        # Min Error Level
        self.min_error_level = QComboBox()
        self.min_error_level.addItems(["Debug", "Info", "Warning", "Error", "Critical"])
        layout.addRow("Minimum Error Level:", self.min_error_level)

        # Group Similar Errors
        self.group_similar_errors = QCheckBox()
        layout.addRow("Group Similar Errors:", self.group_similar_errors)

        # Error History Size
        self.error_history_size = QSpinBox()
        self.error_history_size.setRange(3, 100)
        self.error_history_size.setSingleStep(3)
        layout.addRow("Error History Size:", self.error_history_size)

        # NEW: Analyze All Errors
        self.analyze_all_errors = QCheckBox()
        layout.addRow("Analyze All Errors:", self.analyze_all_errors)

        self.error_tab.setLayout(layout)

    def toggle_containers(self):
        """Show only the relevant container based on selected API type."""
        self.ollama_container.setVisible(self.ollama_radio.isChecked())
        self.openai_container.setVisible(self.openai_radio.isChecked())
        self.azure_container.setVisible(self.azure_openai_radio.isChecked())

    def load_from_settings(self):
        """Load current settings into dialog fields."""
        # Load API settings
        api_type = self.settings.get("api_type", "ollama")
        if api_type == "ollama":
            self.ollama_radio.setChecked(True)
        elif api_type == "openai":
            self.openai_radio.setChecked(True)
        elif api_type == "azure_openai":
            self.azure_openai_radio.setChecked(True)

        # Ollama
        self.ollama_host_input.setText(self.settings.get("ollama_host", "http://localhost:11434"))
        self.ollama_model_input.setText(self.settings.get("ollama_model", "llama2:latest"))

        # OpenAI
        self.openai_url_input.setText(self.settings.get("openai_api_url", "https://api.openai.com/v1/chat/completions"))
        self.openai_key_input.setText(self.settings.get("openai_api_key", ""))
        self.openai_model_input.setText(self.settings.get("openai_model", "gpt-3.5-turbo"))

        # Azure OpenAI
        self.azure_endpoint_input.setText(self.settings.get("azure_openai_endpoint", "https://your-azure-openai-endpoint/"))
        self.azure_deployment_input.setText(self.settings.get("azure_openai_deployment", "Meta-Llama-3-8B-Instruct"))
        self.azure_api_version_input.setText(self.settings.get("azure_openai_api_version", "2024-05-01-preview"))
        self.azure_api_key_input.setText(self.settings.get("azure_openai_api_key", ""))

        # Load Error settings
        self.error_sensitivity.setCurrentText(self.settings.get("error_sensitivity", "medium"))
        self.auto_intercept.setChecked(self.settings.get("auto_intercept", True))
        self.min_error_level.setCurrentText(self.settings.get("min_error_level", "Warning"))
        self.group_similar_errors.setChecked(self.settings.get("group_similar_errors", True))
        self.error_history_size.setValue(self.settings.get("error_history_size", 3))

        # NEW: load "analyze_all_errors"
        self.analyze_all_errors.setChecked(self.settings.get("analyze_all_errors", False))

        self.toggle_containers()

    def get_settings(self):
        """Retrieve the updated settings into a dictionary."""
        if self.ollama_radio.isChecked():
            api_type = "ollama"
        elif self.openai_radio.isChecked():
            api_type = "openai"
        else:
            api_type = "azure_openai"

        return {
            # API Settings
            "api_type": api_type,
            "ollama_host": self.ollama_host_input.text(),
            "ollama_model": self.ollama_model_input.text(),
            "openai_api_url": self.openai_url_input.text(),
            "openai_api_key": self.openai_key_input.text(),
            "openai_model": self.openai_model_input.text(),
            "azure_openai_endpoint": self.azure_endpoint_input.text(),
            "azure_openai_deployment": self.azure_deployment_input.text(),
            "azure_openai_api_version": self.azure_api_version_input.text(),
            "azure_openai_api_key": self.azure_api_key_input.text(),
            
            # Error Settings
            "error_sensitivity": self.error_sensitivity.currentText(),
            "auto_intercept": self.auto_intercept.isChecked(),
            "min_error_level": self.min_error_level.currentText(),
            "group_similar_errors": self.group_similar_errors.isChecked(),
            "error_history_size": self.error_history_size.value(),

            # NEW: analyze_all_errors
            "analyze_all_errors": self.analyze_all_errors.isChecked(),
        }



    def toggle_fields(self):
        """Enable/disable fields depending on which radio is selected."""
        use_ollama = self.ollama_radio.isChecked()
        use_openai = self.openai_radio.isChecked()
        use_azure = self.azure_openai_radio.isChecked()

        # Ollama Fields
        self.ollama_host_input.setEnabled(use_ollama)
        self.ollama_model_input.setEnabled(use_ollama)

        # OpenAI Fields
        self.openai_url_input.setEnabled(use_openai)
        self.openai_key_input.setEnabled(use_openai)
        self.openai_model_input.setEnabled(use_openai)

        # Azure OpenAI Fields
        self.azure_endpoint_input.setEnabled(use_azure)
        self.azure_deployment_input.setEnabled(use_azure)
        self.azure_api_version_input.setEnabled(use_azure)
        self.azure_api_key_input.setEnabled(use_azure)  # Enable API Key input

