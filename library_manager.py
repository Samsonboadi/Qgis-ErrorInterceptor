import os
import sys
import subprocess
import importlib.util
import logging
from typing import List, Optional

from qgis.core import QgsApplication, QgsMessageLog, Qgis
from qgis.PyQt.QtCore import QSettings

class QGISLibraryManager:
    """
    Manages library installation with one-time check mechanism.
    """

    def __init__(self, requirements_path: Optional[str] = None, plugin_name: str = 'QChatGPT'):
        """
        Initialize the Library Manager with one-time check capability.
        
        :param requirements_path: Path to requirements.txt file. 
        :param plugin_name: Unique identifier for the plugin
        """
        # Set up logging
        self.logger = self._setup_logger()
        
        # Plugin-specific settings key
        self.settings_key = f'/QChatGPT/LibraryCheck/{plugin_name}_libraries_installed'
        
        # Determine requirements file path
        if requirements_path is None:
            # Default to requirements.txt in the same directory as the script
            self.requirements_path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)), 
                'requirements.txt'
            )
        else:
            self.requirements_path = requirements_path

    def _setup_logger(self):
        """
        Set up a logger that writes to both QGIS message log and console.
        """
        logger = logging.getLogger('QChatGPTLibraryManager')
        logger.setLevel(logging.INFO)

        # QGIS Log Handler
        qgis_handler = QGISLogHandler()
        qgis_handler.setLevel(logging.INFO)
        
        # Console Handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)

        # Formatter
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        qgis_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        logger.addHandler(qgis_handler)
        logger.addHandler(console_handler)

        return logger

    def are_libraries_checked(self) -> bool:
        """
        Check if libraries have been installed previously.
        
        :return: True if libraries were already checked/installed, False otherwise
        """
        settings = QSettings()
        return settings.value(self.settings_key, False, type=bool)

    def mark_libraries_checked(self, status: bool = True):
        """
        Mark libraries as checked/installed in settings.
        
        :param status: Status to set (default is True)
        """
        settings = QSettings()
        settings.setValue(self.settings_key, status)

    def get_qgis_python_path(self) -> str:
        """
        Get the path to the QGIS Python environment.
        """
        if QgsApplication.instance() is None:
            raise RuntimeError("QGIS application not initialized.")

        qgis_python_path = os.path.join(QgsApplication.prefixPath(), "python")
        if not os.path.exists(qgis_python_path):
            raise FileNotFoundError(f"QGIS Python path not found at: {qgis_python_path}")

        return qgis_python_path

    def find_pip_executable(self) -> str:
        """
        Find the pip executable in the QGIS Python environment.
        """
        qgis_python_path = self.get_qgis_python_path()
        
        pip_candidates = [
            os.path.join(qgis_python_path, "Scripts", "pip.exe"),  # Windows
            os.path.join(qgis_python_path, "bin", "pip"),          # Unix-like
            "pip",                                                 # System PATH
            "pip3"                                                 # Python 3 specific
        ]

        for pip_path in pip_candidates:
            try:
                subprocess.run([pip_path, "--version"], 
                               stdout=subprocess.PIPE, 
                               stderr=subprocess.PIPE, 
                               check=True)
                return pip_path
            except (subprocess.CalledProcessError, FileNotFoundError):
                continue

        raise FileNotFoundError("Could not find pip executable in QGIS Python environment")

    def read_requirements(self) -> List[str]:
        """
        Read requirements from requirements.txt file.
        """
        if not os.path.exists(self.requirements_path):
            raise FileNotFoundError(f"Requirements file not found: {self.requirements_path}")

        with open(self.requirements_path, 'r') as f:
            return [line.strip() for line in f 
                    if line.strip() and not line.startswith('#')]

    def is_library_installed(self, library_name: str) -> bool:
        """
        Check if a specific library is installed.
        """
        try:
            import_name = library_name.split('==')[0].split('>=')[0].split('<=')[0]
            return importlib.util.find_spec(import_name) is not None
        except ImportError:
            return False

    def install_library(self, library: str) -> bool:
        """
        Install a specific library using pip.
        """
        try:
            pip_executable = self.find_pip_executable()
            
            result = subprocess.run(
                [pip_executable, "install", library],
                capture_output=True,
                text=True,
                check=False
            )

            if result.returncode == 0:
                self.logger.info(f"Successfully installed {library}")
                return True
            else:
                self.logger.error(f"Failed to install {library}. Error: {result.stderr}")
                return False

        except Exception as e:
            self.logger.error(f"Exception during library installation: {e}")
            return False

    def check_and_install_libraries(self, force_recheck: bool = False) -> bool:
        """
        Check and install missing libraries with one-time check mechanism.
        
        :param force_recheck: If True, will recheck libraries even if already checked
        :return: True if all libraries are installed or successfully installed
        """
        # Check if libraries were already checked
        if not force_recheck and self.are_libraries_checked():
            self.logger.info("Libraries have been previously checked. Skipping installation.")
            return True

        try:
            # Read requirements
            required_libraries = self.read_requirements()
            
            # Track installation status
            all_installed = True
            
            for library in required_libraries:
                if not self.is_library_installed(library):
                    self.logger.info(f"Library {library} is missing. Attempting to install...")
                    
                    # Attempt installation
                    if not self.install_library(library):
                        self.logger.error(f"Failed to install {library}")
                        all_installed = False
                else:
                    self.logger.info(f"Library {library} is already installed.")
            
            # Mark libraries as checked
            self.mark_libraries_checked(all_installed)
            
            return all_installed

        except Exception as e:
            self.logger.error(f"Error in library management: {e}")
            return False

class QGISLogHandler(logging.Handler):
    """
    Custom logging handler to write logs to QGIS message log.
    """
    def emit(self, record):
        """
        Write log record to QGIS message log.
        """
        try:
            msg = self.format(record)
            QgsMessageLog.logMessage(msg, 'QChatGPT Library Manager', Qgis.Info)
        except Exception:
            self.handleError(record)

def main():
    """
    Main function to demonstrate library management.
    Can be called when plugin is initialized.
    """
    library_manager = QGISLibraryManager()
    
    try:
        # Check and install libraries
        success = library_manager.check_and_install_libraries()
        
        if success:
            library_manager.logger.info("Library setup complete. All requirements met.")
        else:
            library_manager.logger.warning("Some libraries could not be installed. Plugin may have limited functionality.")
    
    except Exception as e:
        library_manager.logger.error(f"Critical error in library setup: {e}")

# Optional method for forcing a recheck if needed
def force_library_recheck():
    """
    Force a full recheck of libraries, ignoring previous checks.
    """
    library_manager = QGISLibraryManager()
    return library_manager.check_and_install_libraries(force_recheck=True)

if __name__ == "__main__":
    main()