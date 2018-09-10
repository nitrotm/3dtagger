# project.py: project container
#
# author: Antony Ducommun dit Boudry (nitro.tm@gmail.com)
# license: GPL
#

import io, json, math, sys, time

import numpy as np

from plyfile import PlyData, PlyElement

from PySide2.QtCore import Signal, Slot, Qt, QObject, QThreadPool

from scene.scene import Scene
from scene.util import SynchronizedObjectProxy, ObjectProxy

from project.scene import ProjectScene
from project.selection import ProjectSelection
from project.view import ProjectView, ViewCreateTask, ViewPreselectionTask, ExportSelectionTask, ExportViewTask, ExportViewTarget


class Project(QObject):
  progresstick = Signal()

  message = Signal(str)
  stateChanged = Signal()

  redraw = Signal()
  loaded = Signal()
  saved = Signal()
  exported = Signal(object)

  aspectRatio = Signal(float)


  def __init__(self, min_focal=0.5, max_focal=1.0, max_dist=1, max_leafs=1000):
    super(Project, self).__init__()
    self.renderer = SynchronizedObjectProxy(Scene())
    self.min_focal = min_focal
    self.max_focal = max_focal
    self.max_dist = max_dist
    self.max_leafs = max_leafs
    self.scenes = dict()
    self.views = list()
    self.viewIndex = 0

    self.displayRatio = 1.0
    self.clearColor = [0.5, 0.5, 0.5, 1.0]
    self.cloudShaderName = 'cloud-rgb'
    self.cloudShader = ObjectProxy()
    self.maskPointSize = 1.0
    self.maskDistanceRange = [0.0, 1.0]

    self.showAxis = True
    self.showPlane = True
    self.showLocation = True
    self.showBBox = True
    self.showPicture = True

    self.cameraMode = 'perspective'
    self.orthoCameraConfig = None
    self.perspectiveCameraConfig = None

    self.selection = list()
    self.selectionRadius = 1.0

    self.threads = QThreadPool()
    self.threads.setMaxThreadCount(4)

    self.exported.connect(self.onexportresult, type=Qt.QueuedConnection)

    self.progresstick.connect(self.onprogress, type=Qt.QueuedConnection)
    self.progresscount = 0
    self.progresstotal = 0
    self.progressbegin = 0
    self.progressui = None
    self.progresscb = None


  def create(self):
    self.ortho2dCamera = self.renderer.getOrtho2DCamera('ortho2d')
    self.orthoCamera = self.renderer.getOrthoCamera('ortho')
    if self.orthoCameraConfig:
      self.orthoCamera.load(self.orthoCameraConfig)
    self.perspectiveCamera = self.renderer.getPerspectiveCamera('perspective')
    if self.perspectiveCameraConfig:
      self.perspectiveCamera.load(self.perspectiveCameraConfig)
    self.renderer.setDefaultCamera(self.perspectiveCamera)

    self.renderer.clearColor = self.clearColor

    self.cloudShader.apply(self.renderer.getShader(self.cloudShaderName))

    axis = self.renderer.addAxis('axis', pointSize=10.0, lineWidth=5.0)
    if not self.showAxis:
      axis.hide()
    plane = self.renderer.addPlane('plane')
    if not self.showPlane:
      plane.hide()
    picture = self.renderer.addQuad('picture', color=(0, 0, 0))
    picture.uniforms['colorMask'] = [1.0, 1.0, 1.0, 0.5]
    if not self.showPicture:
      picture.hide()

    defaultPass = self.renderer.addPass('default', order=0)
    # defaultPass.depthTest = False
    defaultPass.attachNode(axis)
    defaultPass.attachNode(plane)

    overlayPass = self.renderer.addPass('overlay', self.ortho2dCamera, order=100)
    overlayPass.depthMask = False
    overlayPass.depthTest = False
    overlayPass.cullFace = False
    overlayPass.disable()
    overlayPass.attachNode(picture)

    self.setCameraMode(self.cameraMode)

    self.stateChanged.emit()
    self.redraw.emit()


  def preselect(self, progressui=None):
    tasks = list()
    for view in self.views:
      if not view.active or view.built:
        continue
      tasks.append(ViewPreselectionTask(self, view))
    self.startbatch(tasks, progressui)


  def load(self, filename, progressui=None):
    tasks = list()
    with io.open(filename, 'r') as f:
      data = json.load(f)
      if 'version' not in data or data['version'] != 'tagger 1.0':
        raise Exception("unsupported file version")

      self.displayRatio = data['displayRatio'] if 'displayRatio' in data else 1.0
      self.clearColor = data['clearColor'] if 'clearColor' in data else (0.5, 0.5, 0.5, 1.0)
      self.cloudShaderName = data['cloudShaderName'] if 'cloudShaderName' in data else 'cloud'
      self.maskPointSize = data['maskPointSize'] if 'maskPointSize' in data else 1.0
      self.maskDistanceRange = data['maskDistanceRange'] if 'maskDistanceRange' in data else [0.0, 1.0]

      self.showAxis = data['showAxis']
      self.showPlane = data['showPlane']
      self.showLocation = data['showLocation']
      self.showBBox = data['showBBox']
      self.showPicture = data['showPicture']

      self.cameraMode = data['cameraMode']
      self.orthoCameraConfig = data['orthoCamera']
      self.perspectiveCameraConfig = data['perspectiveCamera']

      self.selectionRadius = data['selectionRadius'] if 'selectionRadius' in data else 1.0
      for selection in data['selection']:
        self.selection.append(
          ProjectSelection(
            selection['pt'],
            selection['radius'],
            selection['add'],
            selection['time']
          )
        )
      for item in data['scenes']:
        views = dict()
        for item2 in item['views']:
          views[item2['id']] = ProjectView(
            self,
            item2['name'],
            item2['id'],
            item2['active'],
            item2['density'],
            item2['opacity']
          )
        scene = ProjectScene(self, item['name'], item['path'], views)
        self.scenes[item['path']] = scene

    views = list()
    for scene in sorted(self.scenes.values(), key=lambda x: x.name):
      views += sorted(scene.views.values(), key=lambda x: x.name)
    self.views += views

    self.create()
    for scene in self.scenes.values():
      scene.create()
      for view in scene.views.values():
        tasks.append(ViewCreateTask(self, scene, view))

    self.message.emit('Project loaded.')
    self.loaded.emit()

    self.startbatch(tasks, progressui)


  def save(self, filename):
    data = dict()
    data['version'] = 'tagger 1.0'

    data['displayRatio'] = self.displayRatio
    data['clearColor'] = self.clearColor
    data['cloudShaderName'] = self.cloudShaderName
    data['maskPointSize'] = self.maskPointSize
    data['maskDistanceRange'] = self.maskDistanceRange

    data['showAxis'] = self.showAxis
    data['showPlane'] = self.showPlane
    data['showLocation'] = self.showLocation
    data['showBBox'] = self.showBBox
    data['showPicture'] = self.showPicture

    data['cameraMode'] = self.cameraMode
    data['orthoCamera'] = self.orthoCamera.save()
    data['perspectiveCamera'] = self.perspectiveCamera.save()

    data['selectionRadius'] = self.selectionRadius
    selection = list()
    for item in self.selection:
      selection.append({
        'pt': item.pt,
        'radius': item.radius,
        'add': item.add,
        'time': item.time
      })
    data['selection'] = selection
    scenes = list()
    for item in self.scenes.values():
      views = list()
      for item2 in item.views.values():
        views.append({
          'name': item2.name,
          'id': item2.id,
          'active': item2.active,
          'density': item2.density,
          'opacity': item2.opacity
        })
      scenes.append({
        'name': item.name,
        'path': str(item.path),
        'views': views
      })
    data['scenes'] = scenes
    with io.open(filename, 'w') as f:
      json.dump(data, f, indent='  ')

    self.message.emit('Project saved.')
    self.saved.emit()


  def close(self, gl):
    self.threads.clear()
    self.threads.waitForDone()
    for item in self.scenes.values():
      item.destroy()
    self.renderer.destroy()
    self.renderer.oncleanup(gl)
    self.scenes = dict()
    self.selection = list()
    self.views = list()

    self.message.emit('Project closed.')
    self.stateChanged.emit()
    self.redraw.emit()


  def importmve(self, path, progressui=None):
    if path in self.scenes:
      return

    tasks = list()
    scene = ProjectScene(self, 'mve.%d' % time.time(), path)
    scene.create()
    for view in scene.views.values():
      tasks.append(ViewCreateTask(self, scene, view))
    self.scenes[path] = scene

    self.views += sorted(scene.views.values(), key=lambda x: x.name)

    self.message.emit('MVE scene imported.')
    self.loaded.emit()

    self.startbatch(tasks, progressui)


  def exportply(self, filename, progressui=None):
    tasks = list()
    for view in self.views:
      if not view.active:
        continue
      tasks.append(ExportSelectionTask(self, view))

    self.exportFilename = filename
    self.exportQueue = tasks
    self.exportResults = list()
    self.startbatch(tasks, progressui)

  @Slot(object)
  def onexportresult(self, result):
    self.exportResults.append(result)
    if len(self.exportResults) < len(self.exportQueue):
      return

    el = PlyElement.describe(
      np.concatenate(self.exportResults),
      'vertex'
    )
    PlyData([el]).write(self.exportFilename)

    del self.exportFilename
    del self.exportQueue
    del self.exportResults

    self.message.emit('Selection exported.')


  def exportviews(self, ctx, filename, progressui=None):
    target = ExportViewTarget(self, filename, ctx)

    tasks = list()
    for view in self.views:
      if not view.active:
        continue
      tasks.append(ExportViewTask(self, view, target))

    self.startbatch(tasks, progressui, lambda : target.destroy() )


  def removeView(self, index):
    if index < 0 or index >= len(self.views):
      return
    view = self.views[index]
    view.active = False
    view.destroy()
    self.setCameraView()

    self.message.emit('View %s removed.' % view.name)
    self.redraw.emit()

  def removeCurrentView(self):
    if self.cameraMode == 'view':
      self.removeView(self.viewIndex)


  def startbatch(self, tasks, progressui, callback=None):
    if len(tasks) > 0:
      self.progresscount = 0
      self.progresstotal = len(tasks)
      self.progressbegin = time.time()
      self.progressui = progressui
      self.progresscb = callback
      if self.progressui:
        self.progressui.setModal(True)
        self.progressui.setAutoReset(False)
        self.progressui.setAutoClose(False)
        self.progressui.setValue(1)
        self.progressui.setLabelText("task started...")
        self.progressui.show()
      for task in tasks:
        self.threads.start(task)
    else:
      self.progresscount = 0
      self.progresstotal = 0
      self.progressui = None
      self.progresscb = None

  @Slot()
  def onprogress(self):
    self.progresscount += 1
    count = self.progresscount
    total = self.progresstotal
    begin = self.progressbegin
    ui = self.progressui
    if self.progresscb and count >= total:
      self.progresscb()
      self.progresscb = None
    if not ui:
      return
    if count < total:
      ratio = count / total
      ui.setValue(min(100, max(1, 100 * ratio)))

      dt = time.time() - begin
      remaining = dt / max(0.01, ratio) - dt
      minutes = math.floor(remaining / 60)
      seconds = int(remaining) % 60
      ui.setLabelText("%d / %d (%d:%02d remaining)" % (self.progresscount, self.progresstotal, minutes, seconds))
    else:
      ui.setLabelText("task complete")
      ui.setValue(100)
      ui.close()
      self.progresscount = 0
      self.progresstotal = 0
      self.progressui = None


  @Slot(str)
  def setCameraMode(self, mode):
    if mode == 'ortho':
      self.renderer.setDefaultCamera(self.orthoCamera)
    elif mode == 'perspective':
      self.renderer.setDefaultCamera(self.perspectiveCamera)
    elif mode == 'view':
      if len(self.views) == 0:
        return
      self.cameraMode = mode
      self.setCameraView()
      return
    else:
      raise Exception("invalid camera mode")

    for view in self.views:
      if not view.mesh:
        continue
      view.mesh.pointSize = 2.0
      view.mesh.selectedPointSize = 5.0
      view.mesh.displayRatio = self.displayRatio

    self.cameraMode = mode
    self.renderer.getPass('overlay').disable()
    self.renderer.getNode('picture').hide()
    self.aspectRatio.emit(0)

    self.message.emit('Active camera: %s' % mode)
    self.stateChanged.emit()
    self.redraw.emit()

  @Slot(int)
  def setCameraView(self, di=0):
    index = (self.viewIndex + di) % len(self.views)
    i = 0
    if di >= 0:
      while i < len(self.views) and not self.views[index].valid():
        index = (index + 1) % len(self.views)
        i += 1
    elif di < 0:
      while i < len(self.views) and not self.views[index].valid():
        index = (index - 1) % len(self.views)
        i += 1
    self.setCameraViewAbs(index)

  @Slot(ProjectView)
  def setCameraViewRef(self, view):
    for i in range(len(self.views)):
      if view != self.views[i]:
        continue
      self.setCameraViewAbs(i)
      break

  @Slot(int)
  def setCameraViewAbs(self, index=0):
    index = index % len(self.views)
    if self.cameraMode != 'view':
      return
    if not self.views[index].valid():
      self.setCameraMode('ortho')
      return

    self.viewIndex = index
    view = self.views[self.viewIndex]
    self.renderer.setDefaultCamera(view.camera)

    self.renderer.getPass('overlay').enable()
    if self.showPicture and view.camera.atOrigin and view.width > 0:
      self.renderer.getNode('picture').attachTexture(
        self.renderer.getTexture(view.info.depthcolor())
      )
      self.renderer.getNode('picture').show()
    else:
      self.renderer.getNode('picture').hide()

    if view.width > 0:
      self.aspectRatio.emit(view.height / view.width)
    else:
      self.aspectRatio.emit(0)

    for view2 in self.views:
      if not view2.mesh:
        continue
      if view == view2:
        view2.mesh.pointSize = 4.0
        view2.mesh.selectedPointSize = 5.0
        view2.mesh.displayRatio = 1.0
      else:
        view2.mesh.pointSize = 3.0
        view2.mesh.selectedPointSize = 5.0
        view2.mesh.displayRatio = self.displayRatio

    self.message.emit('Active camera: view (%s)' % view.name)
    self.stateChanged.emit()
    self.redraw.emit()


  @Slot(bool)
  def setCameraAtOrigin(self, allCameras=False):
    self.renderer.defaultCamera.origin()
    if allCameras:
      self.orthoCamera.origin()
      self.perspectiveCamera.origin()
      for view in self.views:
        if not view.camera:
          continue
        view.camera.origin()

    self.redraw.emit()

  @Slot(float, float, float)
  def moveCamera(self, dx=0.0, dy=0.0, dz=0.0):
    self.renderer.defaultCamera.move(dx, dy, dz)

    self.redraw.emit()

  @Slot(float, float, float)
  def orientCamera(self, dyaw=0.0, dpitch=0.0, droll=0.0):
    self.renderer.defaultCamera.orient(dyaw, dpitch, droll)

    self.redraw.emit()

  @Slot(float)
  def zoomCamera(self, dfov=0.0):
    self.renderer.defaultCamera.zoom(dfov)

    self.redraw.emit()


  @Slot()
  def toggleAxis(self):
    self.showAxis = not self.showAxis
    if self.showAxis:
      self.renderer.getNode('axis').show()
    else:
      self.renderer.getNode('axis').hide()

    self.stateChanged.emit()
    self.redraw.emit()

  @Slot()
  def togglePlane(self):
    self.showPlane = not self.showPlane
    if self.showPlane:
      self.renderer.getNode('plane').show()
    else:
      self.renderer.getNode('plane').hide()

    self.stateChanged.emit()
    self.redraw.emit()

  @Slot()
  def toggleLocation(self):
    self.showLocation = not self.showLocation
    for view in self.views:
      if not view.camera:
        continue
      if self.showLocation:
        view.camera.show()
      else:
        view.camera.hide()

    self.stateChanged.emit()
    self.redraw.emit()

  @Slot()
  def toggleBBox(self):
    self.showBBox = not self.showBBox
    for view in self.views:
      if not view.bbox:
        continue
      if self.showBBox:
        view.bbox.show()
      else:
        view.bbox.hide()

    self.stateChanged.emit()
    self.redraw.emit()

  @Slot()
  def togglePicture(self):
    self.showPicture = not self.showPicture
    if self.cameraMode == 'view':
      self.views[self.viewIndex].camera.origin()
      self.setCameraView()

    self.stateChanged.emit()
    self.redraw.emit()


  @Slot(float)
  def setDisplayRatio(self, ratio=1.0):
    self.displayRatio = max(0.0, min(1.0, ratio))

    for view in self.views:
      if not view.mesh:
        continue
      if self.cameraMode == 'view' and self.views[self.viewIndex] == view:
        view.mesh.displayRatio = 1.0
      else:
        view.mesh.displayRatio = self.displayRatio

    self.stateChanged.emit()
    self.redraw.emit()


  @Slot(object)
  def setClearColor(self, color):
    self.clearColor = color
    self.renderer.clearColor = color

    self.redraw.emit()


  @Slot(str)
  def setCloudShader(self, name):
    self.cloudShaderName = name
    self.cloudShader.apply(self.renderer.getShader(name))

    self.redraw.emit()


  @Slot(float)
  def setMaskPointSize(self, size=1.0):
    self.maskPointSize = max(0.0, min(100.0, size))

    self.redraw.emit()


  @Slot(float)
  def setMaskDistanceRange(self, value):
    self.maskDistanceRange[1] = max(self.maskDistanceRange[0], value)

    self.redraw.emit()


  @Slot(float, float, float, bool)
  def select(self, x=0.0, y=0.0, z=0.0, add=True):
    click = ProjectSelection(
      [x, y, z],
      self.selectionRadius if add else self.selectionRadius * 1.25,
      add,
      int(time.time() * 1000)
    )
    changed = False
    for scene in self.scenes.values():
      changed = scene.select([click]) or changed
    if changed:
      self.selection.append(click)
      self.redraw.emit()


  def depth(self, gl, x, y, width, height):
    return self.renderer.depth(gl, x, y, width, height)


  def project(self, pt):
    return self.renderer.defaultCamera.project(pt)


  def unproject(self, gl, x, y, width, height):
    z = self.depth(gl, x, y, width, height)
    return self.renderer.defaultCamera.unproject(x, y, z, 1.0)


  def render(self, gl, width, height, uniforms):
    t = time.time()
    if self.renderer.hasNode('picture'):
      uniforms['pictureOverlay'] = [self.renderer.getNode('picture').visible]
    uniforms['maskPointSize'] = [self.maskPointSize, 0.0]
    uniforms['maskDistanceRange'] = self.maskDistanceRange
    self.renderer.render(gl, width, height, uniforms)
    print('render:%d [ms]' % ((time.time() - t) * 1000))
