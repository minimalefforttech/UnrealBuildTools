from PySide6 import QtCore, QtGui, QtQml
from PySide6.QtWidgets import QApplication
import os
import sys
from pathlib import Path

from unreal_build_tools.core.platform_utils import get_base_path, get_ue_versions
from .models.icon_model import IconModel
from .models.filter_model import IconFilterModel

# Suppress PNG warnings
os.environ['QT_LOGGING_RULES'] = '*.debug=false;qt.gui.imageio.png=false;qt.gui.imageio=false'
os.environ['PNG_NO_WARNINGS'] = '1'

class Console(QtCore.QObject):
    @QtCore.Slot(str)
    def log(self, message):
        print(message)

class ClipboardService(QtCore.QObject):
    @QtCore.Slot(str)
    def copy(self, text):
        clipboard = QtGui.QGuiApplication.clipboard()
        clipboard.setText(text)

class SettingsService(QtCore.QObject):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.settings = QtCore.QSettings("UnrealIconBrowser", "Settings")
    
    @QtCore.Slot(float)
    def saveIconSize(self, size):
        self.settings.setValue("iconSize", size)
        
    @QtCore.Slot(float, result=float)
    def loadIconSize(self, defaultSize):
        return self.settings.value("iconSize", defaultSize, type=float)

def run_app(versions=None, base_path=None, icon_types=None):
    base_path = base_path or get_base_path()
    icon_types = icon_types or ['svg', 'png']
    versions = versions or get_ue_versions(base_path)
    app = QApplication(sys.argv)
    engine = QtQml.QQmlApplicationEngine()
    sub_path = os.path.join("Engine", "Content", "Editor", "Slate")
    
    # Create models with CLI parameters
    icon_model = IconModel(
        versions=versions,
        base_path=base_path,
        sub_path=sub_path,
        icon_types=icon_types
    )
    
    filter_model = IconFilterModel()
    filter_model.setSourceModel(icon_model)
    
    # Register services with QML
    console = Console()
    clipboard_service = ClipboardService()
    engine.rootContext().setContextProperty("console", console)
    engine.rootContext().setContextProperty("clipboardService", clipboard_service)
    
    # Register settings service
    settings_service = SettingsService()
    engine.rootContext().setContextProperty("settingsService", settings_service)
    
    # Register other context properties
    engine.rootContext().setContextProperty("iconModel", filter_model)
    engine.rootContext().setContextProperty("versions", versions)
    engine.rootContext().setContextProperty("basePath", str(base_path))
    engine.rootContext().setContextProperty("subPath", str(sub_path))
    
    # Load QML
    qml_path = Path(__file__).parent / "qml" / "main.qml"
    engine.load(str(qml_path))
    
    if not engine.rootObjects():
        return -1
        
    return app.exec()
