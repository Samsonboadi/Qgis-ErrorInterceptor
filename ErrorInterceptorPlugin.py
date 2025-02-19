# ErrorInterceptorPlugin.py

import os
import json
import sys
import traceback
import re
import platform
from PyQt5.QtWidgets import QAction
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt
from qgis.core import QgsApplication, Qgis, QgsProject

from .GlobalLogger import GlobalLogger
from .LoggingConnector import QGISActionLogger
from .FloatingChatWidget import FloatingChatWidget

from .library_manager import QGISLibraryManager
class ErrorInterceptorPlugin:
    def __init__(self, iface):
        """
        Main plugin class for the QGIS Error Interceptor plugin.
        :param iface: QgisInterface - The QGIS interface instance.
        """
        self.iface = iface
        self.plugin_dir = os.path.dirname(__file__)
        self.toolbar = None
        self.chat_widget = None

                        # Initialize library manager
        self.library_manager = QGISLibraryManager()
        

        if self.library_manager.check_and_install_libraries():
            # Handle library installation success
            self.iface.messageBar().pushMessage(
                "Success", 
                "Required libraries installed successfully", 
                level=Qgis.Success)
        else:
            # Handle library installation failure
            self.iface.messageBar().pushMessage(
                "Error", 
                "Could not install required libraries", 
                level=Qgis.Critical
            )

        # Initialize logger
        self.global_logger = GlobalLogger.get_instance()
        self.logger = self.global_logger.get_logger()

        # Initialize action logger
        try:
            self.action_logger = QGISActionLogger(self.iface)
        except Exception as e:
            self.logger.error(f"Error initializing QGISActionLogger: {str(e)}")

        # Enhanced error tracking
        self.error_count = 0
        self.error_threshold = 3  # Number of similar errors before triggering analysis
        self.recent_errors = []  # List of recent error messages

        # Default settings
        self.settings = {
            "api_type": "ollama",  # or "openai" or "azure_openai"
            "ollama_host": "http://localhost:11434",  # Endpoint for Ollama
            "ollama_model": "llama2:latest",
            "openai_api_url": "https://api.openai.com/v1/chat/completions",
            "openai_api_key": "",
            "openai_model": "gpt-3.5-turbo",
            # Azure OpenAI settings
            "azure_openai_endpoint": "https://your-azure-openai-endpoint/",
            "azure_openai_deployment": "Meta-Llama-3-8B-Instruct",
            "azure_openai_api_version": "2024-05-01-preview",
            "azure_openai_api_key": "",
            # Error Interceptor settings
            "error_sensitivity": "medium",  # low, medium, high
            "auto_intercept": True,
            "min_error_level": "Warning",  # Store as string
            "group_similar_errors": True,
            "error_history_size": 50
        }

        # Store the original excepthook
        self.original_excepthook = sys.excepthook
        # Override the excepthook with the plugin's handler
        sys.excepthook = self.handle_python_exception

    def initGui(self):
        """Initialize the GUI of the plugin."""
        self.load_config()

        if not self.toolbar:
            self.toolbar = self.iface.addToolBar('ErrorInterceptorPlugin')
            self.toolbar.setObjectName('ErrorInterceptorPlugin')

        icon_path = os.path.join(self.plugin_dir, "resources", "icon.png")
        self.action = QAction(QIcon(icon_path), 'Error Interceptor', self.iface.mainWindow())
        self.action.triggered.connect(self.run)
        self.toolbar.addAction(self.action)

        # Connect QGIS log messages to auto-intercept errors
        QgsApplication.messageLog().messageReceived.connect(self.handle_qgis_error)

    def unload(self):
        """Unload the plugin."""
        self.save_config()

        if self.action:
            self.toolbar.removeAction(self.action)
            self.action = None

        if self.toolbar:
            self.iface.mainWindow().removeToolBar(self.toolbar)
            self.toolbar = None

        # Disconnect QGIS logs
        QgsApplication.messageLog().messageReceived.disconnect(self.handle_qgis_error)

        if self.chat_widget:
            self.chat_widget.close()
            self.chat_widget = None

        # Restore the original excepthook
        sys.excepthook = self.original_excepthook

    def run(self):
        """Open or show the floating chat widget."""
        if self.chat_widget:
            self.chat_widget.show()
            self.chat_widget.raise_()
            self.chat_widget.activateWindow()
            return

        self.chat_widget = FloatingChatWidget(self, self.iface, self.settings)
        self.chat_widget.show()

    def handle_qgis_error(self, message, tag, level):
        """Enhanced error handling with proper logging integration"""
        try:
            self.logger.debug(f"Received QGIS log message: {message}, Tag: {tag}, Level: {level}")

            if not self._should_process_error(message, tag, level):
                return

            # Get comprehensive error context
            error_context = self.global_logger.get_error_context()
            
            # Add additional error details
            error_context.update({
                'message': message,
                'tag': tag,
                'level': level,
                # Log levels are already included in get_error_context()
                'recent_actions': self.action_logger.get_recent_actions() if hasattr(self, 'action_logger') else [],
                'system_info': {
                    'qgis_version': Qgis.QGIS_VERSION,
                    'os': f"{platform.system()} {platform.release()}",
                    'python_version': platform.python_version()
                },
                'project_info': self._get_project_info()
            })

            # Group similar errors if enabled
            if self.settings.get("group_similar_errors", True):
                if self._is_duplicate_error(error_context):
                    self.error_count += 1
                    if self.error_count < self.error_threshold:
                        return

            # Create or show chat widget
            if not self.chat_widget:
                self.run()

            if self.chat_widget:
                self.chat_widget.add_error_message(error_context)

                # Show and focus the widget
                if not self.chat_widget.isVisible():
                    self.chat_widget.show()
                    self.chat_widget.raise_()
                    self.chat_widget.activateWindow()

        except Exception as e:
            self.logger.error(f"Error in handle_qgis_error: {str(e)}")
            traceback.print_exc()

    def _get_project_info(self):
        """Gather current QGIS project information"""
        project = QgsProject.instance()
        active_layer = self.iface.activeLayer()
        
        return {
            'filename': project.fileName() or "Unnamed Project",
            'layer_count': len(project.mapLayers()),
            'active_layer': active_layer.name() if active_layer else "None",
            'crs': project.crs().authid() if project.crs() else "Not Set",
            'layers': [layer.name() for layer in project.mapLayers().values()]
        }

    def _should_process_error(self, message, tag, level):
        """Determine if an error should be processed based on settings"""
        # Define levels to exclude
        exclude_levels = [Qgis.Success, Qgis.Info]

        # If you want to analyze absolutely everything, you can remove
        # the exclude_levels check or leave as is:
        if level in exclude_levels:
            return False

        # NEW: If "analyze_all_errors" is enabled, skip all other checks.
        if self.settings.get("analyze_all_errors", False):
            return True

        # Get minimum error level from settings
        min_level_name = self.settings.get("min_error_level", "Warning")
        min_level = getattr(Qgis, min_level_name, Qgis.Warning)

        if level < min_level:
            return False

        # Check if auto-intercept is enabled
        if not self.settings.get("auto_intercept", True):
            return False

        # Apply sensitivity filtering
        sensitivity = self.settings.get("error_sensitivity", "medium")
        if sensitivity == "low" and level < Qgis.Critical:
            return False
        elif sensitivity == "medium" and level < Qgis.Warning:
            return False

        return True



    def _get_error_context(self, message, tag, level):
        """Gather comprehensive context about the error"""
        project = QgsProject.instance()

        context = {
            'message': message,
            'tag': tag,
            'level': level,
            'timestamp': self.global_logger.get_timestamp(),
            'project_file': project.fileName() if project else "No project",
            'active_layer': self.iface.activeLayer().name() if self.iface.activeLayer() else "No active layer",
            'recent_actions': self.action_logger.get_recent_actions(),
            'error_history': self.global_logger.get_error_context(),
            'qgis_version': Qgis.QGIS_VERSION,
        }

        return context

    def _is_duplicate_error(self, error_context):
        """Check if this error is similar to recent errors"""
        for recent_error in self.recent_errors:
            if (recent_error['tag'] == error_context['tag'] and
                self._similar_messages(recent_error['message'], error_context['message'])):
                return True

        # Add to recent errors
        self.recent_errors.append(error_context)
        if len(self.recent_errors) > self.settings.get("error_history_size", 50):
            self.recent_errors.pop(0)

        return False

    def _similar_messages(self, msg1, msg2):
        """Compare two error messages for similarity"""
        # Remove variable parts like memory addresses and timestamps
        msg1 = self._normalize_error_message(msg1)
        msg2 = self._normalize_error_message(msg2)
        return msg1 == msg2

    def _normalize_error_message(self, message):
        """Normalize error message by removing variable parts"""
        # Remove memory addresses
        message = re.sub(r'0x[0-9a-fA-F]+', '', message)
        # Remove timestamps
        message = re.sub(r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}', '', message)
        # Remove file paths
        message = re.sub(r'(?:[a-zA-Z]\:)?(?:\\|\/)[\w\-\. \\\/]+', '', message)
        return message.strip()

    def handle_python_exception(self, exc_type, exc_value, exc_traceback):
        """Handle uncaught Python exceptions"""
        try:
            # Format the traceback
            tb_string = ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))

            # Create error context
            error_context = {
                'message': str(exc_value),
                'tag': 'Python Exception',
                'level': Qgis.Critical,
                'traceback': tb_string,
                'exception_type': exc_type.__name__,
                'context': self.global_logger.get_error_context()
            }

            # Add timestamp from GlobalLogger
            error_context['context'].update({
                'timestamp': self.global_logger.get_timestamp()
            })

            # Log the error
            self.logger.error(f"Uncaught Python Exception: {tb_string}")

            # Print to QGIS Python Console
            print(f"Uncaught Python Exception: {tb_string}")

            # Show in chat widget
            if not self.chat_widget:
                self.run()

            if self.chat_widget:
                self.chat_widget.add_error_message(error_context)

        except Exception as e:
            # If our handling fails, use the original excepthook
            self.logger.error(f"Error in handle_python_exception: {str(e)}")
            # Print the exception to the QGIS Python Console
            print(f"Error in handle_python_exception: {str(e)}")
            self.original_excepthook(exc_type, exc_value, exc_traceback)

        # Always call the original excepthook to ensure proper error handling
        self.original_excepthook(exc_type, exc_value, exc_traceback)

    # ----------------------
    # Config persistence
    # ----------------------

    def load_config(self):
        """Load plugin settings from JSON."""
        config_path = os.path.join(self.plugin_dir, 'settings.json')
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self.settings.update(data)
                self.logger.debug("Plugin settings loaded successfully.")
                print("Plugin settings loaded successfully.")
            except Exception as e:
                self.logger.error(f"Could not load settings.json: {e}")
                print(f"Could not load settings.json: {e}")

    def save_config(self):
        """Save plugin settings to JSON."""
        config_path = os.path.join(self.plugin_dir, 'settings.json')
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=2)
            self.logger.debug("Plugin settings saved successfully.")
            print("Plugin settings saved successfully.")
        except Exception as e:
            self.logger.error(f"Could not save settings.json: {e}")
            print(f"Could not save settings.json: {e}")
