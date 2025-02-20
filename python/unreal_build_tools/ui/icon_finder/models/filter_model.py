from PySide6 import QtCore
import os

from unreal_build_tools.ui.icon_finder.constants import RelativePathRole

class IconFilterModel(QtCore.QSortFilterProxyModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._filter_text = ""
        self.setDynamicSortFilter(True)
        
    @QtCore.Slot(str)
    def setFilterText(self, text):
        self._filter_text = text.lower()
        self.invalidateFilter()
    
    def filterAcceptsRow(self, source_row, source_parent):
        if not self._filter_text:
            return True
            
        source_index = self.sourceModel().index(source_row, 0, source_parent)
        item_path = self.sourceModel().data(source_index, RelativePathRole)
        return self._filter_text in os.path.basename(item_path).lower()
