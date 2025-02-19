import logging
import sys
import os
import time
from datetime import datetime
from logging import Handler
from logging.handlers import RotatingFileHandler
from qgis.core import QgsProject
from qgis.core import Qgis

class InMemoryLogHandler(Handler):
    def __init__(self, capacity=300):
        super().__init__()
        self.log_records = []
        self.capacity = capacity
        self.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

    def emit(self, record):
        try:
            log_entry = self.format(record)
            if len(self.log_records) >= self.capacity:
                self.log_records.pop(0)  # Remove oldest log
            self.log_records.append(log_entry)
        except Exception as e:
            sys.stderr.write(f"Error in InMemoryLogHandler.emit: {str(e)}\n")

    def get_logs(self):
        try:
            return "\n".join(self.log_records)
        except Exception:
            return "Error retrieving logs"

    def clear(self):
        self.log_records = []

class QGISLogFilter(logging.Filter):
    """Filter to add QGIS-specific context to log records"""
    def filter(self, record):
        try:

            record.qgis_version = Qgis.QGIS_VERSION
            record.project_file = QgsProject.instance().fileName() or "Unsaved Project"
            record.layer_count = len(QgsProject.instance().mapLayers())
        except:
            record.qgis_version = "Unknown"
            record.project_file = "Unknown"
            record.layer_count = 0
        return True

class GlobalLogger:
    _instance = None
    _initialized = False

    @staticmethod
    def get_instance():
        if GlobalLogger._instance is None:
            GlobalLogger()
        return GlobalLogger._instance

    def __init__(self):
        if GlobalLogger._instance is not None:
            raise Exception("GlobalLogger is a singleton! Use get_instance() instead.")
        else:
            GlobalLogger._instance = self
            # Initialize member variables before setup
            self.logger = None
            self.memory_handler = None
            self.console_handler = None
            self.file_handler = None
            self.error_handler = None
            
            if not self._initialized:
                self.setup_logger()
                GlobalLogger._initialized = True

    # Convenience logging methods
    def log(self, message, level=logging.INFO):
        """Convenience method to log messages at any level"""
        if self.logger is None:
            self.setup_logger()
        self.logger.log(level, message)

    def debug(self, message):
        """Convenience method for debug logging"""
        if self.logger is None:
            self.setup_logger()
        self.logger.debug(message)

    def info(self, message):
        """Convenience method for info logging"""
        if self.logger is None:
            self.setup_logger()
        self.logger.info(message)

    def warning(self, message):
        """Convenience method for warning logging"""
        if self.logger is None:
            self.setup_logger()
        self.logger.warning(message)

    def error(self, message):
        """Convenience method for error logging"""
        if self.logger is None:
            self.setup_logger()
        self.logger.error(message)

    def critical(self, message):
        """Convenience method for critical logging"""
        if self.logger is None:
            self.setup_logger()
        self.logger.critical(message)

    def setup_logger(self):
        try:
            # Create logger
            self.logger = logging.getLogger("GeomindsLogger")
            self.logger.setLevel(logging.DEBUG)
            
            # Prevent duplicate logging
            if self.logger.handlers:
                self.logger.handlers.clear()

            # Add QGIS context filter
            qgis_filter = QGISLogFilter()
            self.logger.addFilter(qgis_filter)

            # Create logs directory if it doesn't exist
            log_dir = os.path.join(os.path.expanduser("~"), ".qgis3", "geominds_logs")
            os.makedirs(log_dir, exist_ok=True)

            # Setup formatters
            detailed_formatter = logging.Formatter(
                '%(asctime)s - %(levelname)s - [QGIS v%(qgis_version)s] - '
                'Project: %(project_file)s - Layers: %(layer_count)d - '
                '%(message)s'
            )
            console_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

            # Initialize handlers with error handling for each
            try:
                # In-Memory Handler (initialize first since other methods depend on it)
                self.memory_handler = InMemoryLogHandler(capacity=1000)
                self.memory_handler.setLevel(logging.DEBUG)
                self.memory_handler.setFormatter(detailed_formatter)
                self.logger.addHandler(self.memory_handler)
            except Exception as e:
                sys.stderr.write(f"Failed to initialize memory_handler: {str(e)}\n")
                self.memory_handler = None

            # Console Handler
            if sys.stdout:
                try:
                    self.console_handler = logging.StreamHandler(sys.stdout)
                    self.console_handler.setLevel(logging.WARNING)
                    self.console_handler.setFormatter(console_formatter)
                    self.logger.addHandler(self.console_handler)
                except Exception as e:
                    sys.stderr.write(f"Failed to initialize console_handler: {str(e)}\n")
                    self.console_handler = None

            # Log initialization
            self.logger.info("GlobalLogger initialized successfully")
            
        except Exception as e:
            sys.stderr.write(f"Failed to initialize GlobalLogger: {str(e)}\n")
            raise

    def get_logger(self):
        """Returns the logger instance. Creates it if it doesn't exist."""
        if self.logger is None:
            self.setup_logger()
        return self.logger

    def get_memory_logs(self, last_n=None, level=None):
        """
        Get logs from memory with optional filtering
        :param last_n: Optional number of last N logs to retrieve
        :param level: Optional log level to filter by
        :return: String of filtered logs
        """
        if self.memory_handler is None:
            return "Error: Memory handler not initialized"
            
        try:
            logs = self.memory_handler.log_records
            if level:
                logs = [log for log in logs if level.upper() in log]
            if last_n:
                logs = logs[-last_n:]
            return "\n".join(logs)
        except Exception as e:
            return f"Error retrieving logs: {str(e)}"

    def get_timestamp(self):
        """Returns the current timestamp as a formatted string."""
        return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

    def clear_memory_logs(self):
        """Clear in-memory logs"""
        if self.memory_handler:
            self.memory_handler.clear()

    def get_error_context(self):
        """Get recent logs as context for error analysis"""
        try:
            recent_logs = self.get_memory_logs(last_n=1)  # Last 50 log entries
            return {
                'recent_logs': recent_logs,
                'timestamp': self.get_timestamp(),
                'log_levels_count': {
                    'ERROR': recent_logs.count('ERROR'),
                    'WARNING': recent_logs.count('WARNING'),
                    'DEBUG': recent_logs.count('DEBUG')
                }
            }
        except Exception as e:
            return {'error': f"Failed to get error context: {str(e)}"}

    def clear_memory_logs(self):
        """Clear in-memory logs"""
        self.memory_handler.clear()


