from qgis.core import (
    QgsProject,
    QgsApplication,
    Qgis,
    QgsMapLayer
)
from qgis.gui import QgsMapCanvas
from PyQt5.QtCore import QObject
from PyQt5.QtWidgets import QAction
from functools import partial
import platform
import traceback

from .GlobalLogger import GlobalLogger

class QGISActionLogger(QObject):
    def __init__(self, iface):
        """Initialize the logger with QGIS interface."""
        super().__init__()
        self.iface = iface
        
        # Enhanced logging setup
        try:
            self.logger = GlobalLogger.get_instance().get_logger()
            print("GlobalLogger instance obtained successfully")
        except Exception as e:
            print(f"Error obtaining GlobalLogger: {e}")
            self.logger = None
        
        # Add action history tracking
        self.action_history = []
        self.max_history = 20  # Keep last 100 actions
        
        try:
            print("Attempting to connect signals...")
            self.connect_signals()
            print("Signals connected successfully")
        except Exception as e:
            #print(f"Error initializing QGISActionLogger: {e}")
            #print(traceback.format_exc())
            if self.logger:
                self.logger.error(f"Error initializing QGISActionLogger: {str(e)}")

    def add_to_history(self, action_type, details):
        """Add an action to the history with comprehensive error handling."""
        try:
            # Ensure we have a valid timestamp
            timestamp = GlobalLogger.get_instance().get_timestamp()
            
            # Create the action dictionary
            action = {
                'timestamp': timestamp,
                'type': action_type,
                'details': details
            }
            
            # Add extensive logging
            #print(f"Adding action - Type: {action_type}, Details: {details}")
            
            # Append the action to history
            self.action_history.append(action)
            
            # Log the current history size
            #print(f"Current action history size: {len(self.action_history)}")
            
            # Maintain history size
            if len(self.action_history) > self.max_history:
                removed_action = self.action_history.pop(0)
                print(f"Removed oldest action: {removed_action}")
            
            # Log to file if logger is available
            if self.logger:
                self.logger.info(f"Action logged: {action_type} - {details}")
        
        except Exception as e:
            # More detailed error logging
            #print(f"FULL Error adding action to history: {e}")
            #print(traceback.format_exc())
            if self.logger:
                self.logger.error(f"Error adding action to history: {str(e)}")

    def get_recent_actions(self, n=5):
        """Retrieve the n most recent actions with enhanced error handling."""
        try:
            recent = self.action_history[-n:] if self.action_history else []
            #print(f"Retrieving {n} recent actions. Total actions: {len(self.action_history)}")
            
            formatted_actions = [
                f"{action['timestamp']} - {action['type']}: {action['details']}" 
                for action in recent
            ]
            
            #print("Formatted recent actions:", formatted_actions)
            return formatted_actions
        
        except Exception as e:
            #print(f"Error retrieving recent actions: {e}")
            #print(traceback.format_exc())
            if self.logger:
                self.logger.error(f"Error retrieving recent actions: {str(e)}")
            return []

    def safe_log_layers(self, message, *args):
        """Safely log information about multiple layers with enhanced logging."""
        try:
            if not args:
                print(f"No args received for: {message}")
                self.add_to_history("LayerOperation", "No layers affected")
                return

            if len(args) == 1 and isinstance(args[0], (list, tuple)):
                layers = args[0]
                layer_names = ", ".join([l.name() for l in layers if l])
                #print(f"Logging layers: {layer_names}")
                self.add_to_history("LayerOperation", f"{message}: {layer_names}")
            else:
                #print(f"Logging layer args: {args}")
                self.add_to_history("LayerOperation", f"{message}: {args}")

        except Exception as e:
            #print(f"Error logging layers: {e}")
            #print(traceback.format_exc())
            if self.logger:
                self.logger.error(f"Error logging layers: {str(e)}")

    def on_action_triggered(self, action, checked=False):
        """Handle QAction triggers with comprehensive logging."""
        try:
            action_text = action.text().strip()
            if action_text:  # Only log non-empty action names
                #print(f"Action triggered: {action_text}")
                self.add_to_history("UserAction", f"Triggered: {action_text}")
        except Exception as e:
            #rint(f"Error logging action: {e}")
            #print(traceback.format_exc())
            if self.logger:
                self.logger.error(f"Error logging action: {str(e)}")

    def connect_signals(self):
        """
        Connects QGIS signals with comprehensive debug logging.
        """
        print("Initializing signal connections...")
        
        project = QgsProject.instance()
        map_canvas = self.iface.mapCanvas()

        # Signal connection tracking
        connection_attempts = 0
        successful_connections = 0

        # Connect QGIS message log signal
        try:
            QgsApplication.messageLog().messageReceived.connect(self.on_qgis_message)
            print("Connected to QGIS message log signal")
            successful_connections += 1
        except Exception as e:
            print(f"Failed to connect QGIS message log signal: {e}")

        # Connect QAction triggers
        try:
            actions = self.iface.mainWindow().findChildren(QAction)
            print(f"Found {len(actions)} actions to connect")
            
            for action in actions:
                try:
                    action.triggered.connect(lambda checked, a=action: self.on_action_triggered(a, checked))
                    connection_attempts += 1
                    successful_connections += 1
                except Exception as action_connect_error:
                    print(f"Failed to connect action {action.text()}: {action_connect_error}")
        
        except Exception as e:
            print(f"Error finding and connecting actions: {e}")

        print(f"Signal Connection Summary:")
        print(f"Total Connection Attempts: {connection_attempts}")
        print(f"Successful Connections: {successful_connections}")

    def on_qgis_message(self, message, tag, level):
        """Handle QGIS messages from the global message log."""
        try:
            level_name = self.get_level_name(level)
            print(f"QGIS Message [{level_name}] {tag}: {message}")
            self.add_to_history("QGISMessage", f"[{level_name}] {tag}: {message}")
        except Exception as e:
            print(f"Error processing QGIS message: {e}")
            print(traceback.format_exc())
            if self.logger:
                self.logger.error(f"Error processing QGIS message: {str(e)}")

    @staticmethod
    def get_level_name(level):
        """Convert QGIS message level to string representation."""
        level_mapping = {
            Qgis.Info: "INFO",
            Qgis.Warning: "WARNING",
            Qgis.Critical: "CRITICAL",
            Qgis.Success: "SUCCESS",
        }
        return level_mapping.get(level, "UNKNOWN")