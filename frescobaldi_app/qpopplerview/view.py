# This file is part of the qpopplerview package.
#
# Copyright (c) 2010, 2011 by Wilbert Berendsen
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
# See http://www.gnu.org/licenses/ for more information.


"""
View widget to display PDF documents.
"""


from PyQt4.QtCore import *
from PyQt4.QtGui import *

import popplerqt4

from . import surface
from . import cache


# viewModes:
FixedScale = 0
FitWidth   = 1
FitHeight  = 2
FitBoth    = FitHeight | FitWidth


class View(QScrollArea):
    
    viewModeChanged = pyqtSignal(int)
    
    def __init__(self, parent=None):
        super(View, self).__init__(parent)
        
        self.setAlignment(Qt.AlignCenter)
        
        p = self.viewport().palette()
        p.setBrush(QPalette.Background, p.dark())
        self.viewport().setPalette(p)
        
        self._viewMode = FixedScale
        
        # delayed resize
        self._newsize = None
        self._resizeTimer = QTimer(singleShot = True, timeout = self._resizeTimeout)
    
    def surface(self):
        """Returns our Surface, the widget drawing the page(s)."""
        sf = self.widget()
        if not sf:
            sf = surface.Surface(self)
            self.setSurface(sf)
        return sf
    
    def setSurface(self, sf):
        """Sets the given surface as our widget."""
        self.setWidget(sf)
    
    def viewMode(self):
        """Returns the current ViewMode."""
        return self._viewMode
        
    def setViewMode(self, mode):
        """Sets the current ViewMode."""
        if mode == self._viewMode:
            return
        self._viewMode = mode
        if mode:
            pass # TODO: change view if necessary for the mode
        self.viewModeChanged.emit(mode)
    
    def load(self, document):
        """Convenience method to load all the pages from the given Poppler.Document."""
        self.surface().pageLayout().load(document)
        self.surface().pageLayout().update()
        self.surface().updateLayout()

    def clear(self):
        """Convenience method to clear the current layout."""
        self.surface().pageLayout().clear()
        self.surface().pageLayout().update()
        self.surface().updateLayout()

    def setScale(self, scale):
        """Sets the scale of all pages in the View."""
        self.surface().pageLayout().setScale(scale)
        self.surface().pageLayout().update()
        self.surface().updateLayout()

    def visiblePages(self):
        """Yields the visible pages."""
        rect = self.viewport().rect()
        rect.translate(-self.surface().pos())
        rect.intersect(self.surface().rect())
        return self.surface().pageLayout().pagesAt(rect)

    def redraw(self):
        """Redraws, e.g. when you changed rendering hints or papercolor on the document."""
        pages = list(self.visiblePages())
        documents = set(page.document() for page in pages)
        for document in documents:
            cache.clear(document)
        for page in pages:
            cache.generate(page)

    def resizeEvent(self, ev):
        super(View, self).resizeEvent(ev)
        if self.viewMode() and self.surface().pageLayout().count():
            self.resizeWithDelay(ev.size())
            
    def resizeWithDelay(self, size):
        self._newsize = size
        self._resizeTimer.start(100)
        
    def _resizeTimeout(self):
        layout = self.surface().pageLayout()
        scales = []
        if self.viewMode() & FitWidth:
            scales.append(layout.widest().scaleForWidth(self._newsize.width() - layout.margin() * 2))
        if self.viewMode() & FitHeight:
            scales.append(layout.heighest().scaleForHeight(self._newsize.height() - layout.margin() * 2))
        self.setScale(min(scales))


