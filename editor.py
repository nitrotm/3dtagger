# editor.py: shader editor
#
# author: Antony Ducommun dit Boudry (nitro.tm@gmail.com)
# license: GPL
#

import io, re

from pathlib import Path

from PySide2.QtCore import Qt, Signal, Slot, QPoint, QSize
from PySide2.QtGui import QColor, QSyntaxHighlighter, QTextOption, QWindow
from PySide2.QtWidgets import (
  QAction, QColorDialog, QHBoxLayout, QInputDialog, QLabel, QLineEdit, QPlainTextEdit,
  QPushButton, QSlider, QTextEdit, QVBoxLayout, QWidget
)


class Editor(QWidget):
  changed = Signal()

  def __init__(self, parent):
    super(Editor, self).__init__(parent)

    self.path = Path(__file__).parent / 'shaders'
    self.project = None
    self.programName = None
    self.vertexShader = ''
    self.fragmentShader = ''

    self.colorEditor = QLineEdit()
    self.colorEditor.setEnabled(False)
    self.colorEditor.textChanged.connect(self.updateColorHex)
    self.updateColor((0.5, 0.5, 0.5, 1.0))

    self.pickButton = QPushButton('Pick')
    self.pickButton.setEnabled(False)
    self.pickButton.clicked.connect(self.pickColor)

    colorContainer = QWidget()
    colorContainer.setLayout(QHBoxLayout())
    colorContainer.layout().setMargin(0)
    colorContainer.layout().addWidget(self.colorEditor)
    colorContainer.layout().addWidget(self.pickButton)

    self.displayRatioSlider = QSlider(Qt.Horizontal)
    self.displayRatioSlider.setRange(0, 1000)
    self.displayRatioSlider.setEnabled(False)
    self.displayRatioSlider.setSingleStep(1)
    self.displayRatioSlider.setPageStep(10)
    self.displayRatioSlider.valueChanged.connect(self.updateDisplayRatio)

    self.pointSizeSlider = QSlider(Qt.Horizontal)
    self.pointSizeSlider.setRange(0, 500)
    self.pointSizeSlider.setEnabled(False)
    self.pointSizeSlider.setSingleStep(1)
    self.pointSizeSlider.setPageStep(10)
    self.pointSizeSlider.valueChanged.connect(self.updatePointSize)

    self.distanceSlider = QSlider(Qt.Horizontal)
    self.distanceSlider.setRange(0, 1000)
    self.distanceSlider.setEnabled(False)
    self.distanceSlider.setSingleStep(1)
    self.distanceSlider.setPageStep(10)
    self.distanceSlider.valueChanged.connect(self.updateDistanceRange)

    self.vertexEditor = QPlainTextEdit()
    self.vertexEditor.setStyleSheet("QPlainTextEdit { background: #393939; color: #b6dede; font: 1rem 'monospace'; }")
    self.vertexEditor.setLineWrapMode(QPlainTextEdit.NoWrap)
    self.vertexEditor.setWordWrapMode(QTextOption.NoWrap)
    self.vertexEditor.setTabStopWidth(2)
    self.vertexEditor.setTabChangesFocus(False)
    self.vertexEditor.setCenterOnScroll(True)
    self.vertexEditor.setEnabled(False)
    self.vertexEditor.textChanged.connect(self.saveVertex)

    self.fragmentEditor = QPlainTextEdit()
    self.fragmentEditor.setStyleSheet("QPlainTextEdit { background: #393939; color: #b6dede; font: 1rem 'monospace'; }")
    self.fragmentEditor.setLineWrapMode(QPlainTextEdit.NoWrap)
    self.fragmentEditor.setWordWrapMode(QTextOption.NoWrap)
    self.fragmentEditor.setTabStopWidth(2)
    self.fragmentEditor.setTabChangesFocus(False)
    self.fragmentEditor.setCenterOnScroll(True)
    self.fragmentEditor.setEnabled(False)
    self.fragmentEditor.textChanged.connect(self.saveFragment)

    self.setLayout(QVBoxLayout())
    self.layout().addWidget(QLabel("Display (%):"))
    self.layout().addWidget(self.displayRatioSlider)
    self.layout().addWidget(QLabel("Mask Point size (px):"))
    self.layout().addWidget(self.pointSizeSlider)
    self.layout().addWidget(QLabel("Mask Distance range:"))
    self.layout().addWidget(self.distanceSlider)
    self.layout().addWidget(QLabel("Clear color:"))
    self.layout().addWidget(colorContainer)
    self.layout().addWidget(QLabel("Vertex shader:"))
    self.layout().addWidget(self.vertexEditor)
    self.layout().addWidget(QLabel("Fragment shader:"))
    self.layout().addWidget(self.fragmentEditor)


  def setProject(self, project):
    self.project = project
    if project:
      self.displayRatioSlider.setValue(project.displayRatio * 1000)
      self.displayRatioSlider.setEnabled(True)
      self.pointSizeSlider.setValue(project.maskPointSize * 10)
      self.pointSizeSlider.setEnabled(True)
      self.distanceSlider.setValue(project.maskDistanceRange[1] * 10)
      self.distanceSlider.setEnabled(True)
      self.updateColor(project.clearColor)
      self.loadShader(project.cloudShaderName)
      self.colorEditor.setEnabled(True)
      self.pickButton.setEnabled(True)
      self.vertexEditor.setEnabled(True)
      self.fragmentEditor.setEnabled(True)
    else:
      self.displayRatioSlider.setValue(1000)
      self.displayRatioSlider.setEnabled(False)
      self.pointSizeSlider.setValue(10)
      self.pointSizeSlider.setEnabled(False)
      self.distanceSlider.setValue(10)
      self.distanceSlider.setEnabled(False)
      self.updateColor((0.5, 0.5, 0.5, 1.0))
      self.clearShader()
      self.colorEditor.setEnabled(False)
      self.pickButton.setEnabled(False)
      self.vertexEditor.setEnabled(False)
      self.fragmentEditor.setEnabled(False)


  def parseColorHex(self, value):
    m = re.compile('#?([0-9a-f]{2})([0-9a-f]{2})([0-9a-f]{2})([0-9a-f]{2})').match(value)
    if not m:
      return None
    return (
      min(max(int(m.group(1), base=16), 0), 255) / 255.0,
      min(max(int(m.group(2), base=16), 0), 255) / 255.0,
      min(max(int(m.group(3), base=16), 0), 255) / 255.0,
      min(max(int(m.group(4), base=16), 0), 255) / 255.0
    )

  def pickColor(self):
    color = QColor()
    color.setRgbF(*self.parseColorHex(self.colorEditor.text()))
    color = QColorDialog.getColor(color, parent=self, title="Background Color", options=QColorDialog.ShowAlphaChannel)
    if not color.isValid():
      return
    self.updateColor(
      (
        color.redF(),
        color.greenF(),
        color.blueF(),
        color.alphaF()
      )
    )

  def updateColorHex(self, value):
    self.updateColor(self.parseColorHex(value))

  def updateColor(self, color):
    def formatChannel(value):
      return "%02x" % int(min(max(value * 255.0, 0.0), 255.0))
    bg = "#%s%s%s" % (formatChannel(color[0]), formatChannel(color[1]), formatChannel(color[2]))
    fg = "#ffffff" if sum(color) / 3 < 0.5 else "#000000"
    self.colorEditor.setStyleSheet("QLineEdit { color: %s; background: %s; }" % (fg, bg))
    text = bg + formatChannel(color[3])
    if self.colorEditor.text() != text:
      self.colorEditor.setText(text)
    if self.project:
      self.project.setClearColor(color)
    # self.changed.emit()

  def updateDisplayRatio(self, value):
    if self.project:
      self.project.setDisplayRatio(value / 1000.0)
    # self.changed.emit()

  def updatePointSize(self, value):
    if self.project:
      self.project.setMaskPointSize(value / 10.0)
    # self.changed.emit()

  def updateDistanceRange(self, value):
    if self.project:
      self.project.setMaskDistanceRange(value / 10.0)
    # self.changed.emit()


  def clearShader(self):
    self.programName = None
    self.vertexShader = ''
    self.fragmentShader = ''
    self.vertexEditor.setPlainText('')
    self.fragmentEditor.setPlainText('')

  def loadShader(self, name):
    self.programName = name
    self.vertexShader = ''
    self.fragmentShader = ''
    try:
      with io.open(self.path / (self.programName + '.vs'), 'r') as f:
        self.vertexShader = f.read()
    except Exception as e:
      print(e)
    try:
      with io.open(self.path / (self.programName + '.fs'), 'r') as f:
        self.fragmentShader = f.read()
    except Exception as e:
      print(e)
    self.vertexEditor.setPlainText(self.vertexShader)
    self.fragmentEditor.setPlainText(self.fragmentShader)

  def saveVertex(self):
    value = self.vertexEditor.toPlainText()
    if not self.programName or self.vertexShader == value:
      return
    with io.open(self.path / (self.programName + '.vs'), 'w') as f:
      f.write(value)
    self.vertexShader = value
    self.changed.emit()

  def saveFragment(self):
    value = self.fragmentEditor.toPlainText()
    if not self.programName or self.fragmentShader == value:
      return
    with io.open(self.path / (self.programName + '.fs'), 'w') as f:
      f.write(value)
    self.fragmentShader = value
    self.changed.emit()
