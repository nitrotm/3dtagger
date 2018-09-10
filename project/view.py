# view.py: project view container
#
# author: Antony Ducommun dit Boudry (nitro.tm@gmail.com)
# license: GPL
#

import cv2, gzip, io, json, lzma, math, sys, time

import numpy as np
import scipy.spatial as sp

from plyfile import PlyData, PlyElement

from PySide2.QtCore import QMutex, QRunnable, QThread
from PySide2.QtGui import QImage, QOpenGLContext, QOpenGLFramebufferObject, QOffscreenSurface, QSurfaceFormat

from OpenGL import GL

from project.cloud import ProjectCloud


class ProjectView(object):
  EXPORT_DTYPE = [
    ('x', 'f4'), ('y', 'f4'), ('z', 'f4'),
    ('red', 'u1'), ('green', 'u1'), ('blue', 'u1'), ('alpha', 'u1')
  ]


  def __init__(self, project, name, id, active=True, density=1.0, opacity=1.0):
    self.project = project
    self.name = name
    self.id = id
    self.active = active
    self.density = density
    self.opacity = opacity
    self.info = None
    self.created = False
    self.width = 0
    self.height = 0
    self.camera = None
    self.cloud = ProjectCloud()
    self.mesh = None
    self.bbox = None
    self.built = False
    self.kdtree = None


  def valid(self):
    return self.active and self.camera

  def create(self, keep_ply=True):
    self.destroy()
    self.created = True
    if not self.info or not self.info.valid():
      return
    self.width = self.info.depthWidth
    self.height = self.info.depthHeight
    plyfilename = self.info.ply()
    self.active = self.active and plyfilename != None and self.info.robust(self.project.min_focal, self.project.max_focal, self.project.max_dist)
    if self.active:
      self.camera = self.project.renderer.getViewCamera(self.name, self.info, color=(1.0, 1.0, 0.0))

      self.loadply(plyfilename)

      bcenter = (self.cloud.bbox2 + self.cloud.bbox1) / 2
      bsize = self.cloud.bbox2 - self.cloud.bbox1
      self.bbox = self.project.renderer.addBBox('bbox:%s' % self.name, bsize)
      self.bbox.translate(bcenter[0], bcenter[1], bcenter[2])
      if not self.project.showBBox:
        self.bbox.hide()

      self.mesh = self.project.renderer.addPointCloud('cloud:%s' % self.name, 2.0, self.project.displayRatio)
      self.mesh.setData(self.cloud.count, self.cloud.vertices, self.cloud.colors[:,0:3].copy())

      if not keep_ply:
        self.cloud.unload()
    else:
      self.camera = self.project.renderer.getViewCamera(self.name, self.info, lineWidth=0.0, color=(1.0, 0.0, 1.0))
    if not self.project.showLocation:
      self.camera.hide()

  def destroy(self):
    self.created = False
    self.width = 0
    self.height = 0
    if self.camera:
      self.project.renderer.removeNode(self.camera.name)
      self.camera = None
    self.cloud.unload()
    if self.mesh:
      self.project.renderer.removeNode(self.mesh.name)
      self.mesh = None
    if self.bbox:
      self.project.renderer.removeNode(self.bbox.name)
      self.bbox = None
    self.built = False
    self.kdtree = None

  def buildindex(self):
    if self.cloud.count > 0:
      self.kdtree = sp.cKDTree(self.cloud.vertices, self.project.max_leafs)
    self.built = True

  def select(self, clicks):
    if not self.built or not self.kdtree:
      return False
    changed = False
    for click in clicks:
      indices = self.kdtree.query_ball_point(click.pt, click.radius)
      changed = self.mesh.updateSelection(indices, click.add) or changed
    return changed

  def loadply(self, filename):
    if filename.endswith('.xz'):
      with lzma.open(filename) as f:
        self.cloud.load(PlyData.read(f))
    elif filename.endswith('.gz'):
      with gzip.open(filename) as f:
        self.cloud.load(PlyData.read(f))
    else:
      with io.open(filename, 'rb') as f:
        self.cloud.load(PlyData.read(f))

  def exportSelection(self, clicks):
    if not self.active or not self.mesh or self.cloud.count == 0:
      return np.zeros((0,), dtype=ProjectView.EXPORT_DTYPE)
    indices = list(self.mesh.selectedIndices)
    a = np.zeros((len(indices),), dtype=ProjectView.EXPORT_DTYPE)
    a['x'] = self.cloud.vertices[indices,0]
    a['y'] = self.cloud.vertices[indices,1]
    a['z'] = self.cloud.vertices[indices,2]
    a['red'] = self.cloud.colors[indices,0]
    a['green'] = self.cloud.colors[indices,1]
    a['blue'] = self.cloud.colors[indices,2]
    a['alpha'] = self.cloud.colors[indices,3]
    return a

  def exportImage(self, target):
    if not self.active:
      return

    fbo = QOpenGLFramebufferObject(self.info.width, self.info.height)
    fbo.setAttachment(QOpenGLFramebufferObject.Depth)
    if not fbo.bind():
      raise Exception("Failed to bind framebuffer")
    try:
      depth = target.render(self)

      fbo.toImage().save(str(self.info.path / (target.filename + ".png")))

      cv2.imwrite(
        str(self.info.path / (target.filename + "-depth.png")),
        (depth * 65535.0).astype(np.uint16)
      )
    finally:
      fbo.release()


class ViewCreateTask(QRunnable):
  def __init__(self, project, scene, view):
    super(ViewCreateTask, self).__init__()
    self.project = project
    self.scene = scene
    self.view = view

  def run(self):
    try:
      if not self.view.created:
        self.view.create()
        if self.view.camera:
          self.scene.renderPass.attachNode(self.view.camera)
        if self.view.bbox:
          self.scene.renderPass.attachNode(self.view.bbox)
        if self.view.mesh:
          self.scene.cloudRenderPass.attachNode(self.view.mesh)

      self.project.message.emit("View %s built." % self.view.name)
      self.project.redraw.emit()
    finally:
      self.project.progresstick.emit()


class ViewPreselectionTask(QRunnable):
  def __init__(self, project, view):
    super(ViewPreselectionTask, self).__init__()
    self.project = project
    self.view = view

  def run(self):
    try:
      if self.view.active and not self.view.built:
        self.view.buildindex()
        self.view.select(self.project.selection)

      self.project.message.emit("View %s processed." % self.view.name)
      self.project.redraw.emit()
    finally:
      self.project.progresstick.emit()


class ExportSelectionTask(QRunnable):
  def __init__(self, project, view):
    super(ExportSelectionTask, self).__init__()
    self.project = project
    self.view = view

  def run(self):
    try:
      data = self.view.exportSelection(self.project.selection)

      self.project.message.emit("View's selection %s exported." % self.view.name)
      self.project.exported.emit(data)
    finally:
      self.project.progresstick.emit()


class ExportViewTarget(object):
  def __init__(self, project, filename, parent):
    self.mutex = QMutex()
    self.project = project
    self.filename = filename
    self.parent = parent
    self.surface = QOffscreenSurface()
    self.surface.setFormat(QSurfaceFormat.defaultFormat())
    self.surface.create()

  def destroy(self):
    self.surface.destroy()

  def render(self, view, uniforms=dict()):
    self.project.setCameraMode('view')
    self.project.setCameraViewRef(view)
    self.project.setCameraAtOrigin()
    self.project.render(self.ctx.functions(), view.info.width, view.info.height, uniforms)
    depth = self.project.renderer.depthmap(self.ctx.functions(), view.info.width, view.info.height)
    return depth

  def __enter__(self):
    self.mutex.lock()
    self.ctx = QOpenGLContext()
    self.ctx.setShareContext(self.parent)
    self.ctx.create()
    if not self.ctx.makeCurrent(self.surface):
      raise Exception("cannot make context current")
    self.project.renderer.lock()

  def __exit__(self, type, value, tb):
    self.project.renderer.unlock()
    self.ctx.doneCurrent()
    del self.ctx
    self.mutex.unlock()


class ExportViewTask(QRunnable):
  def __init__(self, project, view, target):
    super(ExportViewTask, self).__init__()
    self.project = project
    self.view = view
    self.target = target

  def run(self):
    try:
      with self.target as t:
        self.view.exportImage(self.target)

      self.project.message.emit("View's image %s exported." % self.view.name)
    finally:
      self.project.progresstick.emit()
