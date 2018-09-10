# app.py: application entry point
#
# author: Antony Ducommun dit Boudry (nitro.tm@gmail.com)
# license: GPL
#

import sys

from PySide2.QtCore import QCoreApplication, QPoint, QSize, Qt
from PySide2.QtGui import QSurfaceFormat
from PySide2.QtWidgets import QApplication

from window import Window


if __name__ == '__main__':
  fmt = QSurfaceFormat()
  fmt.setRenderableType(QSurfaceFormat.OpenGL)
  fmt.setVersion(2, 1)
  fmt.setProfile(QSurfaceFormat.CoreProfile)
  fmt.setSwapBehavior(QSurfaceFormat.DoubleBuffer)
  fmt.setSwapInterval(1)
  fmt.setStereo(False)
  fmt.setSamples(0)
  fmt.setRedBufferSize(8)
  fmt.setGreenBufferSize(8)
  fmt.setBlueBufferSize(8)
  fmt.setAlphaBufferSize(8)
  fmt.setDepthBufferSize(24)
  fmt.setStencilBufferSize(1)
  QSurfaceFormat.setDefaultFormat(fmt)

  app = QApplication(sys.argv)
  window = Window()
  window.show()
  sys.exit(app.exec_())
