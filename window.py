# window.py: main app window
#
# author: Antony Ducommun dit Boudry (nitro.tm@gmail.com)
# license: GPL
#

import io, json

from pathlib import Path

from PySide2.QtCore import Signal, Slot, Qt, QFile, QFileInfo, QPoint, QRect, QSize
from PySide2.QtGui import QColor, QKeySequence, QIcon, QImage
from PySide2.QtWidgets import (
  QAction, QActionGroup, QDockWidget, QFileDialog, QGridLayout, QHBoxLayout, QInputDialog,
  QMainWindow, QMenu, QMessageBox, QProgressDialog, QToolButton, QVBoxLayout, QWidget
)

from project.project import Project

from editor import Editor
from view import View


class Window(QMainWindow):
  def __init__(self):
    super(Window, self).__init__()

    self.project = None
    self.view = None
    self.lastProjectDirectory = None
    self.lastProjectFile = None
    self.recentProjectFiles = list()
    self.lastImportDirectory = None

    self.loadSettings()

    self.setWindowTitle("Point Cloud Tagger")
    self.createActions()
    self.createMenus()
    self.createToolBars()
    self.createContainer()
    self.createEditor()
    self.createStatusBar()


  def loadSettings(self):
    try:
      with io.open(Path(__file__).parent / 'app.json', 'r') as f:
        data = json.load(f)
        if 'lastProjectDirectory' in data:
          self.lastProjectDirectory = data['lastProjectDirectory']
        if 'recentProjectFiles' in data:
          self.recentProjectFiles = data['recentProjectFiles']
        if 'lastImportDirectory' in data:
          self.lastImportDirectory = data['lastImportDirectory']
    except:
      pass

  def saveSettings(self):
    data = dict()
    data['lastProjectDirectory'] = self.lastProjectDirectory
    data['recentProjectFiles'] = self.recentProjectFiles
    data['lastImportDirectory'] = self.lastImportDirectory
    with io.open(Path(__file__).parent / 'app.json', 'w') as f:
      json.dump(data, f, indent=' ')


  def createActions(self):
    # root = QFileInfo(__file__).absolutePath()
    self.newAct = QAction(
      # QIcon(root + '/icons/new.png'),
      "&New",
      self,
      shortcut=QKeySequence.New,
      statusTip="Start new project",
      triggered=self.newProject
    )
    self.openAct = QAction(
      # QIcon(root + '/icons/open.png'),
      "&Open",
      self,
      shortcut=QKeySequence.Open,
      statusTip="Open project",
      triggered=self.openProject
    )
    self.saveAct = QAction(
      # QIcon(root + '/icons/save.png'),
      "&Save",
      self,
      shortcut=QKeySequence.Save,
      statusTip="Save project",
      triggered=self.saveProject,
      enabled=False
    )
    self.saveAsAct = QAction(
      # QIcon(root + '/icons/saveas.png'),
      "Save &As...",
      self,
      shortcut=QKeySequence.SaveAs,
      statusTip="Save project under new name",
      triggered=self.saveProjectAs,
      enabled=False
    )
    self.closeAct = QAction(
      # QIcon(root + '/icons/close.png'),
      "&Close",
      self,
      shortcut=QKeySequence.Close,
      statusTip="Close project",
      triggered=self.closeProject,
      enabled=False
    )
    self.importAct = QAction(
      # QIcon(root + '/icons/import.png'),
      "Import MVE Scene",
      self,
      statusTip="Import MVE scene",
      triggered=self.importMVEScene,
      enabled=False
    )
    self.exportSelectionAct = QAction(
      # QIcon(root + '/icons/import.png'),
      "Export Selection",
      self,
      statusTip="Export selection to ply",
      triggered=self.exportSelection,
      enabled=False
    )
    self.exportViewsAct = QAction(
      # QIcon(root + '/icons/import.png'),
      "Export Views",
      self,
      statusTip="Export views to png",
      triggered=self.exportViews,
      enabled=False
    )
    self.exitAct = QAction(
      # QIcon(root + '/icons/quit.png'),
      "&Quit",
      self,
      shortcut=QKeySequence.Quit,
      statusTip="Close the application",
      triggered=self.close
    )
    self.aboutAct = QAction(
      "&About",
      self,
      statusTip="Show the application's About box",
      triggered=self.about
    )

    cameraGroup = QActionGroup(self)
    self.orthoCameraAct = QAction(
      # QIcon(root + '/icons/camera-ortho.png'),
      "Orthographic",
      cameraGroup,
      shortcut="O",
      statusTip="Orthographic camera",
      triggered=self.toggleOrthoCamera,
      checkable=True,
      checked=False,
      enabled=False
    )
    self.perspectiveCameraAct = QAction(
      # QIcon(root + '/icons/camera-perpective.png'),
      "Perspective",
      cameraGroup,
      shortcut="P",
      statusTip="Perspective camera",
      triggered=self.togglePerspectiveCamera,
      checkable=True,
      checked=True,
      enabled=False
    )
    self.viewCameraAct = QAction(
      # QIcon(root + '/icons/camera-view.png'),
      "View",
      cameraGroup,
      shortcut="[",
      statusTip="Views camera",
      triggered=self.toggleViewCamera,
      checkable=True,
      checked=False,
      enabled=False
    )
    self.toggleAxisAct = QAction(
      # QIcon(root + '/icons/axis.png'),
      "Axis",
      self,
      statusTip="Show/hide axis",
      triggered=self.toggleAxis,
      checkable=True,
      checked=True,
      enabled=False
    )
    self.togglePlaneAct = QAction(
      # QIcon(root + '/icons/plane.png'),
      "Plane",
      self,
      statusTip="Show/hide plane",
      triggered=self.togglePlane,
      checkable=True,
      checked=True,
      enabled=False
    )
    self.toggleLocationAct = QAction(
      # QIcon(root + '/icons/location.png'),
      "Location",
      self,
      statusTip="Show/hide location",
      triggered=self.toggleLocation,
      checkable=True,
      checked=True,
      enabled=False
    )
    self.toggleBBoxAct = QAction(
      # QIcon(root + '/icons/bbox.png'),
      "BBox",
      self,
      statusTip="Show/hide box",
      triggered=self.toggleBBox,
      checkable=True,
      checked=True,
      enabled=False
    )
    self.togglePhotoAct = QAction(
      # QIcon(root + '/icons/photo.png'),
      "Picture",
      self,
      shortcut="]",
      statusTip="Show/hide picture",
      triggered=self.togglePicture,
      checkable=True,
      checked=True,
      enabled=False
    )

    self.preselectAct = QAction(
      "Build/apply selection",
      self,
      statusTip="Build index and apply saved selection",
      triggered=self.preselect,
      enabled=False
    )
    self.editorAct = QAction(
      "Scene editor",
      self,
      statusTip="Open scene editor",
      triggered=self.showEditor,
      enabled=False
    )

  def createMenus(self):
    fileMenu = self.menuBar().addMenu("&File")
    fileMenu.addAction(self.newAct)
    fileMenu.addAction(self.openAct)
    fileMenu.addAction(self.saveAct)
    fileMenu.addAction(self.saveAsAct)
    fileMenu.addAction(self.closeAct)
    fileMenu.addSeparator()
    fileMenu.addAction(self.importAct)
    fileMenu.addSeparator()
    fileMenu.addAction(self.exportSelectionAct)
    fileMenu.addAction(self.exportViewsAct)
    fileMenu.addSeparator()
    self.recentMenu = fileMenu.addMenu("Recent...")
    self.updateRecentMenu()
    fileMenu.addSeparator()
    fileMenu.addAction(self.exitAct)

    viewMenu = self.menuBar().addMenu("&View")
    viewMenu.addAction(self.orthoCameraAct)
    viewMenu.addAction(self.perspectiveCameraAct)
    viewMenu.addAction(self.viewCameraAct)
    viewMenu.addSeparator()
    viewMenu.addAction(self.toggleAxisAct)
    viewMenu.addAction(self.togglePlaneAct)
    viewMenu.addAction(self.toggleLocationAct)
    viewMenu.addAction(self.toggleBBoxAct)
    viewMenu.addAction(self.togglePhotoAct)
    viewMenu.addSeparator()
    self.shaderMenu = viewMenu.addMenu("Cloud shaders...")
    self.shaderMenu.setEnabled(False)
    self.updateShaderMenu()

    toolsMenu = self.menuBar().addMenu("&Tools")
    toolsMenu.addAction(self.preselectAct)
    toolsMenu.addSeparator()
    toolsMenu.addAction(self.editorAct)

    self.menuBar().addSeparator()
    helpMenu = self.menuBar().addMenu("&Help")
    helpMenu.addAction(self.aboutAct)

  def updateRecentMenu(self):
    self.recentMenu.clear()
    if len(self.recentProjectFiles) > 0:
      for file in self.recentProjectFiles:
        def openRecent(filename):
          return lambda : self.openProject(filename)
        if len(file) > 30:
          name = "..." + file[-30:]
        else:
          name = file
        self.recentMenu.addAction(name, openRecent(file))
    else:
      self.recentMenu.addSection("No project yet")

  def updateShaderMenu(self):
    self.shaderActions = dict()
    self.shaderMenu.clear()
    items = sorted(
      set([ file.stem for file in (Path(__file__).parent / 'shaders').iterdir() if file.is_file() ])
    )
    group = QActionGroup(self)
    for item in items:
      def setShader(name):
        return lambda : self.setCloudShader(name)
      checked = False
      if self.project:
        checked = self.project.cloudShaderName == item
      action = QAction(
        item,
        group,
        triggered=setShader(item),
        checkable=True,
        checked=checked
      )
      self.shaderActions[item] = action
      self.shaderMenu.addAction(action)

  def createToolBars(self):
    # self.fileToolBar = self.addToolBar("File")
    # self.fileToolBar.addAction(self.newAct)
    # self.fileToolBar.addAction(self.openAct)
    # self.fileToolBar.addAction(self.saveAct)

    # viewToolBar = self.addToolBar("View")
    # cameraMenu = QMenu("Camera", self)
    # cameraMenu.addAction(self.orthoCameraAct)
    # cameraMenu.addAction(self.perspectiveCameraAct)
    # cameraMenu.addAction(self.viewCameraAct)
    # cameraButton = QToolButton(text="Camera", popupMode=QToolButton.InstantPopup)
    # cameraButton.setMenu(cameraMenu)
    # viewToolBar.addWidget(cameraButton)
    # viewToolBar.addAction(self.toggleAxisAct)
    # viewToolBar.addAction(self.togglePlaneAct)
    # viewToolBar.addAction(self.toggleLocationAct)
    # viewToolBar.addAction(self.toggleBBoxAct)
    # viewToolBar.addAction(self.togglePhotoAct)
    pass

  def createContainer(self):
    self.container = QWidget(self)
    self.container.setStyleSheet("QOpenGLWidget { background: black; }")
    self.container.setLayout(QVBoxLayout())
    self.setCentralWidget(self.container)

  def createEditor(self):
    self.editor = Editor(self)
    self.editor.changed.connect(self.renderProject, type=Qt.QueuedConnection)

  def createStatusBar(self):
    self.statusBar().showMessage("Initialized")


  def closeEvent(self, event):
    self.destroyProject()
    event.accept()


  def enableProjectActions(self, enabled):
    actions = [
      self.saveAct,
      self.saveAsAct,
      self.closeAct,
      self.importAct,
      self.exportSelectionAct,
      self.exportViewsAct,
      self.orthoCameraAct,
      self.perspectiveCameraAct,
      self.viewCameraAct,
      self.toggleAxisAct,
      self.togglePlaneAct,
      self.toggleLocationAct,
      self.toggleBBoxAct,
      self.togglePhotoAct,
      self.shaderMenu,
      self.preselectAct,
      self.editorAct,
    ]
    for action in actions:
      action.setEnabled(enabled)

  def createProject(self):
    self.destroyProject()
    self.project = Project(0.7, 0.9, 0.1, 1000)
    self.project.message.connect(self.showMessage, type=Qt.QueuedConnection)
    self.project.stateChanged.connect(self.updateState, type=Qt.QueuedConnection)
    self.view = View(self, self.project)
    self.container.layout().addWidget(self.view)
    self.enableProjectActions(True)
    self.updateShaderMenu()
    self.editor.setProject(self.project)

  def destroyProject(self):
    self.editor.setProject(None)
    self.enableProjectActions(False)
    if self.view:
      self.container.layout().removeWidget(self.view)
      self.view.close()
      self.view = None
    if self.project:
      self.project.message.disconnect(self.showMessage)
      self.project.stateChanged.disconnect(self.updateState)
      self.project = None


  @Slot(str)
  def showMessage(self, message):
    self.statusBar().showMessage(message)

  @Slot()
  def updateState(self):
    if not self.project:
      return
    self.orthoCameraAct.setChecked(self.project.cameraMode == 'ortho')
    self.perspectiveCameraAct.setChecked(self.project.cameraMode == 'perspective')
    self.viewCameraAct.setChecked(self.project.cameraMode == 'view')
    self.toggleAxisAct.setChecked(self.project.showAxis)
    self.togglePlaneAct.setChecked(self.project.showPlane)
    self.toggleLocationAct.setChecked(self.project.showLocation)
    self.toggleBBoxAct.setChecked(self.project.showBBox)
    self.togglePhotoAct.setChecked(self.project.showPicture)


  def newProject(self):
    self.createProject()
    self.project.create()
    self.lastProjectFile = None

  def openProject(self, filename=None):
    if not filename:
      (filename, ftype) = QFileDialog.getOpenFileName(
        self,
        "Choose project file",
        dir=self.lastProjectDirectory,
        filter="Projects (*.prj)",
        options=QFileDialog.DontResolveSymlinks | QFileDialog.HideNameFilterDetails
      )
    if filename:
      self.lastProjectDirectory = str(Path(filename).parent)
      self.createProject()
      progress = QProgressDialog('', None, 0, 100, self)
      try:
        self.project.load(filename, progress)
        self.lastProjectFile = filename
        if filename in self.recentProjectFiles:
          self.recentProjectFiles.remove(filename)
        self.recentProjectFiles.insert(0, filename)
        self.updateRecentMenu()
        self.updateShaderMenu()
        self.editor.setProject(self.project)
        self.saveSettings()
      except BaseException as e:
        progress.close()
        raise e

  def saveProject(self):
    if not self.lastProjectFile:
      self.saveProjectAs()
      return
    self.project.save(self.lastProjectFile)

  def saveProjectAs(self):
    (filename, ftype) = QFileDialog.getSaveFileName(
      self,
      "Choose project file",
      dir=self.lastProjectDirectory,
      filter="Projects (*.prj)",
      options=QFileDialog.DontResolveSymlinks | QFileDialog.HideNameFilterDetails
    )
    if filename:
      if not filename.endswith('.prj'):
        filename += '.prj'
      self.project.save(filename)
      self.lastProjectFile = filename
      if filename in self.recentProjectFiles:
        self.recentProjectFiles.remove(filename)
      self.recentProjectFiles.insert(0, filename)
      self.updateRecentMenu()
      self.saveSettings()

  def closeProject(self):
    self.destroyProject()

  def importMVEScene(self):
    (filename, ftype) = QFileDialog.getOpenFileName(
      self,
      "Choose MVE scene",
      dir=self.lastImportDirectory,
      filter="MVE Scene (synth_0.out)",
      options=QFileDialog.DontResolveSymlinks
    )
    if filename:
      directory = str(Path(filename).parent)
      self.lastImportDirectory = directory
      progress = QProgressDialog('', None, 0, 100, self)
      try:
        self.project.importmve(directory, progress)
        self.view.update()
        self.saveSettings()
      except BaseException as e:
        progress.close()
        raise e

  def exportSelection(self):
    (filename, ftype) = QFileDialog.getSaveFileName(
      self,
      "Choose ply file",
      dir=self.lastProjectDirectory,
      filter="Meshes (*.ply)",
      options=QFileDialog.DontResolveSymlinks | QFileDialog.HideNameFilterDetails
    )
    if filename:
      if not filename.endswith('.ply'):
        filename += '.ply'
      progress = QProgressDialog('', None, 0, 100, self)
      try:
        self.project.exportply(filename, progress)
      except BaseException as e:
        progress.close()
        raise e

  def exportViews(self):
    filename, ok = QInputDialog.getText(self, "View Image Filename", "Png filename")
    if ok and len(filename) > 0:
      progress = QProgressDialog('', None, 0, 100, self)
      try:
        self.project.exportviews(self.view.context(), filename, progress)
      except BaseException as e:
        progress.close()
        raise e


  def preselect(self):
    progress = QProgressDialog('', None, 0, 100, self)
    try:
      self.project.preselect(progress)
    except BaseException as e:
      progress.close()
      raise e

  def showEditor(self):
    dock = QDockWidget("Scene Parameters", self)
    dock.setAllowedAreas(Qt.RightDockWidgetArea)
    dock.setFixedWidth(640)
    dock.setWidget(self.editor)
    self.addDockWidget(Qt.RightDockWidgetArea, dock)


  def toggleOrthoCamera(self):
    if not self.orthoCameraAct.isChecked():
      return
    self.project.setCameraMode('ortho')

  def togglePerspectiveCamera(self):
    if not self.perspectiveCameraAct.isChecked():
      return
    self.project.setCameraMode('perspective')

  def toggleViewCamera(self):
    if not self.viewCameraAct.isChecked():
      return
    self.project.setCameraMode('view')

  def toggleAxis(self):
    self.project.toggleAxis()

  def togglePlane(self):
    self.project.togglePlane()

  def toggleLocation(self):
    self.project.toggleLocation()

  def toggleBBox(self):
    self.project.toggleBBox()

  def togglePicture(self):
    self.project.togglePicture()


  def setCloudShader(self, name):
    if not self.project:
      return
    self.editor.loadShader(name)
    self.project.setCloudShader(name)
    self.shaderActions[name].setChecked(True)

  def renderProject(self):
    if not self.project:
      return
    self.project.redraw.emit()


  def about(self):
    QMessageBox.about(self, "About Application", "The <b>3D Tagger</b> can load point-clouds from MVE scenes, tag points and export result.")
