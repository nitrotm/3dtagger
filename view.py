# view.py: opengl viewer
#
# author: Antony Ducommun dit Boudry (nitro.tm@gmail.com)
# license: GPL
#

from PySide2.QtCore import Qt, Signal, Slot, QPoint, QSize
from PySide2.QtGui import QOpenGLFunctions
from PySide2.QtWidgets import QOpenGLWidget

from OpenGL import GL


class View(QOpenGLWidget, QOpenGLFunctions):
  cameraMode    = Signal(str)
  cameraOrigin  = Signal(bool)
  cameraMove    = Signal(float, float, float)
  cameraOrient  = Signal(float, float, float)
  cameraZoom    = Signal(float)
  cameraView    = Signal(int)

  displayRatio  = Signal(float)
  togglePicture = Signal()
  removeView    = Signal()

  selected      = Signal(float, float, float, bool)


  def __init__(self, window, project):
    super(View, self).__init__(window)
    QOpenGLFunctions.__init__(self)

    self.setFocusPolicy(Qt.StrongFocus)
    self.aspectRatio = 0.0
    self.shiftKey = False
    self.ctrlKey = False
    self.lastMousePos = QPoint()

    self.project = project
    self.project.redraw.connect(self.update, type=Qt.QueuedConnection)
    self.project.aspectRatio.connect(self.setAspectRatio, type=Qt.QueuedConnection)
    self.cameraMode.connect(self.project.setCameraMode, type=Qt.QueuedConnection)
    self.cameraOrigin.connect(self.project.setCameraAtOrigin, type=Qt.QueuedConnection)
    self.cameraMove.connect(self.project.moveCamera, type=Qt.QueuedConnection)
    self.cameraOrient.connect(self.project.orientCamera, type=Qt.QueuedConnection)
    self.cameraZoom.connect(self.project.zoomCamera, type=Qt.QueuedConnection)
    self.cameraView.connect(self.project.setCameraView, type=Qt.QueuedConnection)
    self.displayRatio.connect(self.project.setDisplayRatio, type=Qt.QueuedConnection)
    self.togglePicture.connect(self.project.togglePicture, type=Qt.QueuedConnection)
    self.removeView.connect(self.project.removeCurrentView, type=Qt.QueuedConnection)
    self.selected.connect(self.project.select, type=Qt.QueuedConnection)


  @Slot(float)
  def setAspectRatio(self, ratio):
    self.aspectRatio = ratio
    if self.aspectRatio > 0.0:
      self.setFixedHeight(self.width() * self.aspectRatio)
    else:
      self.setMinimumHeight(0)
      self.setMaximumHeight(16777215)

  def destroy(self, *args, **kwds):
    if self.project:
      self.makeCurrent()
      self.project.close(self)
      self.project = None
      self.doneCurrent()
    super(View, self).destroy(*args, **kwds)


  def initializeGL(self):
    self.initializeOpenGLFunctions()
    print(self.glGetString(GL.GL_VENDOR))
    print(self.glGetString(GL.GL_RENDERER))
    print(self.glGetString(GL.GL_VERSION))
    print(self.glGetString(GL.GL_SHADING_LANGUAGE_VERSION))
    # print(self.glGetString(GL.GL_EXTENSIONS))
    self.context().aboutToBeDestroyed.connect(self.destroy)

  def paintGL(self):
    if not self.project:
      return
    uniforms = dict()
    self.project.render(self, self.width(), self.height(), uniforms)

  def resizeGL(self, width, height):
    if self.aspectRatio > 0:
      self.setFixedHeight(self.width() * self.aspectRatio)
    else:
      self.setMinimumHeight(0)
      self.setMaximumHeight(16777215)
    self.update()


  def closeEvent(self, event):
    self.destroy()
    event.accept()

  def keyPressEvent(self, event):
    k = event.key()
    if k == Qt.Key_Shift:
      self.shiftKey = True
    if k == Qt.Key_Control:
      self.ctrlKey = True

    # if k == Qt.Key_O:
    #   self.cameraMode.emit('ortho')
    # elif k == Qt.Key_P:
    #   self.cameraMode.emit('perspective')
    # elif k == Qt.Key_BracketLeft:
    #   self.cameraMode.emit('view')
    if k == Qt.Key_BracketRight:
      self.togglePicture.emit()
    elif k == Qt.Key_Comma:
      self.cameraView.emit(-1)
    elif k == Qt.Key_Period:
      self.cameraView.emit(+1)
    elif k == Qt.Key_I:
      self.cameraOrigin.emit(event.modifiers() & Qt.ShiftModifier)
    elif k == Qt.Key_W:
      self.cameraMove.emit( 0.00,  0.00, -0.25)
    elif k == Qt.Key_S:
      self.cameraMove.emit( 0.00,  0.00,  0.25)
    elif k == Qt.Key_A:
      self.cameraMove.emit(-0.25,  0.00,  0.00)
    elif k == Qt.Key_D:
      self.cameraMove.emit( 0.25,  0.00,  0.00)
    elif k == Qt.Key_R:
      self.cameraMove.emit( 0.00,  0.25,  0.00)
    elif k == Qt.Key_F:
      self.cameraMove.emit( 0.00, -0.25,  0.00)
    elif k == Qt.Key_QuoteLeft:
      self.displayRatio.emit(0.000)
    elif k == Qt.Key_1:
      self.displayRatio.emit(0.001)
    elif k == Qt.Key_2:
      self.displayRatio.emit(0.010)
    elif k == Qt.Key_3:
      self.displayRatio.emit(0.020)
    elif k == Qt.Key_4:
      self.displayRatio.emit(0.050)
    elif k == Qt.Key_5:
      self.displayRatio.emit(0.100)
    elif k == Qt.Key_6:
      self.displayRatio.emit(0.150)
    elif k == Qt.Key_7:
      self.displayRatio.emit(0.250)
    elif k == Qt.Key_8:
      self.displayRatio.emit(0.500)
    elif k == Qt.Key_9:
      self.displayRatio.emit(0.750)
    elif k == Qt.Key_0:
      self.displayRatio.emit(1.000)
    elif k == Qt.Key_X:
      self.removeView.emit()
    else:
      return

  def keyReleaseEvent(self, event):
    k = event.key()
    mod = event.modifiers()
    if k == Qt.Key_Shift:
      self.shiftKey = False
    if k == Qt.Key_Control:
      self.ctrlKey = False

  def mousePressEvent(self, event):
    x = event.x()
    y = event.y()
    self.lastMousePos = event.pos()

    if event.button() == Qt.LeftButton:
      if self.ctrlKey:
        if self.project:
          self.makeCurrent()
          pt = self.project.unproject(self, x, y, self.width(), self.height())
          self.doneCurrent()
          self.selected.emit(pt[0], pt[1], pt[2], not self.shiftKey)

  def mouseMoveEvent(self, event):
    x = event.x()
    y = event.y()
    dx = x - self.lastMousePos.x()
    dy = y - self.lastMousePos.y()
    self.lastMousePos = event.pos()

    if event.buttons() & Qt.LeftButton:
      if self.ctrlKey:
        if self.project:
          self.makeCurrent()
          pt = self.project.unproject(self, x, y, self.width(), self.height())
          self.doneCurrent()
          self.selected.emit(pt[0], pt[1], pt[2], not self.shiftKey)
      elif self.shiftKey:
        self.cameraOrient.emit(0,      dy / 3, dx / 3)
      else:
        self.cameraOrient.emit(dx / 3, dy / 3,      0)
    # elif event.buttons() & Qt.MiddleButton:
    elif event.buttons() & Qt.RightButton:
      self.cameraMove.emit(-dx / 10, dy / 10, 0)

  def wheelEvent(self, event):
    dx = event.angleDelta().x() / 8
    dy = event.angleDelta().y() / 8
    self.cameraZoom.emit(dy / 15)
