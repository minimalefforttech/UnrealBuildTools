from PySide6 import QtCore
from pathlib import Path
import os
import sys
from unreal_build_tools.ui.icon_finder.constants import RelativePathRole

class IconModel(QtCore.QAbstractListModel):
    def __init__(self, versions, base_path, sub_path, icon_types, parent=None):
        super().__init__(parent)
        self._icons = []
        self.versions = versions
        self.base_path = base_path
        self.icon_types = icon_types
        self.sub_path = sub_path
        self.load_icons()
    
    def roleNames(self):
        return {
            QtCore.Qt.DisplayRole: b'display',
            RelativePathRole: b'relativePath'
        }
    
    def rowCount(self, parent=QtCore.QModelIndex()):
        return len(self._icons)
        
    def data(self, index, role):
        if not index.isValid():
            return None
            
        if 0 <= index.row() < self.rowCount():
            if role == QtCore.Qt.DisplayRole:
                return str(self._icons[index.row()])
            elif role == RelativePathRole:
                return str(self._icons[index.row()])
        return None
    
    def load_icons(self):
        """Load only relative paths that exist in all UE versions"""
        version_paths = []
        for version in self.versions:
            if sys.platform == 'darwin':
                version_path = Path(self.base_path) / f"UE_{version}" / self.sub_path
            else:
                version_path = Path(self.base_path) / f"UE_{version}" / self.sub_path
            version_paths.append(version_path)

        if not all(p.exists() for p in version_paths):
            return
            
        first_version = version_paths[0]
        icon_paths = set()
        for pattern in [f'*.{ext}' for ext in self.icon_types]:
            for icon_file in first_version.rglob(pattern):
                icon_paths.add(icon_file.relative_to(first_version))
        
        for version_path in version_paths[1:]:
            existing_paths = set()
            for pattern in [f'*.{ext}' for ext in self.icon_types]:
                for icon_file in version_path.rglob(pattern):
                    existing_paths.add(icon_file.relative_to(version_path))
            icon_paths.intersection_update(existing_paths)
        
        self._icons = sorted(icon_paths)