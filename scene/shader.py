# shader.py: opengl shader program state
#
# author: Antony Ducommun dit Boudry (nitro.tm@gmail.com)
# license: GPL
#

import io, os

from pathlib import Path, PurePath

from PySide2.QtGui import QOpenGLShader, QOpenGLShaderProgram, QMatrix2x2, QMatrix3x3, QMatrix4x4, QQuaternion, QVector2D, QVector3D, QVector4D

from OpenGL import GL

from scene.state import SceneState


class Shader(SceneState):
  def __init__(self, scene, filename):
    super(Shader, self).__init__(scene, filename)
    self.path = Path(__file__).parent.parent / 'shaders'
    self.filename = filename
    self.mtime = 0
    self.program = None


  def toJSON(self):
    data = super(Shader, self).toJSON()
    data['filename'] = self.filename
    return data


  def setAttributeArray(self, name, gltype, offset=0, count=3, stride=0):
    if self.enabled <= 0:
      raise Exception("shader must be enabled")
    self.program.setAttributeBuffer(name, gltype, offset, count, stride)
    self.program.enableAttributeArray(name)

  def unsetAttributeArray(self, name):
    if self.enabled <= 0:
      raise Exception("shader must be enabled")
    self.program.disableAttributeArray(name)

  def setValue(self, name, v):
    if self.enabled <= 0:
      raise Exception("shader must be enabled")
    self.program.setUniformValue(name, v)

  def setValues(self, name, *values):
    if self.enabled <= 0:
      raise Exception("shader must be enabled")
    self.program.setUniformValue(name, *values)

  def setVector2(self, name, v):
    if self.enabled <= 0:
      raise Exception("shader must be enabled")
    self.program.setUniformValue(name, QVector2D(*v.flat))

  def setVector3(self, name, v):
    if self.enabled <= 0:
      raise Exception("shader must be enabled")
    self.program.setUniformValue(name, QVector3D(*v.flat))

  def setVector4(self, name, v):
    if self.enabled <= 0:
      raise Exception("shader must be enabled")
    self.program.setUniformValue(name, QVector4D(*v.flat))

  def setMatrix4x4(self, name, m):
    if self.enabled <= 0:
      raise Exception("shader must be enabled")
    self.program.setUniformValue(name, QMatrix4x4(*m.flat))

  def setUniforms(self, uniforms):
    if self.enabled <= 0:
      raise Exception("shader must be enabled")
    for (name, values) in uniforms.items():
      self.program.setUniformValue(name, *values)


  def oncleanup(self):
    for item in list(self.deps):
      item.detachShader(self)
    super(Shader, self).oncleanup()


  def createimpl(self, gl):
    if not self.filename:
      raise Exception("missing program filename")
    self.program = QOpenGLShaderProgram()
    self.mtime = max(
      os.stat(self.path / ('%s.vs' % self.filename)).st_mtime,
      os.stat(self.path / ('%s.fs' % self.filename)).st_mtime
    )
    with io.open(self.path / ('%s.vs' % self.filename), 'r') as f:
      self.program.addShaderFromSourceCode(QOpenGLShader.Vertex, f.read())
    with io.open(self.path / ('%s.fs' % self.filename), 'r') as f:
      self.program.addShaderFromSourceCode(QOpenGLShader.Fragment, f.read())
    if not self.program.link():
      raise Exception("invalid program")

  def updateimpl(self, gl):
    if not self.filename:
      raise Exception("missing program filename")
    mtime = max(
      os.stat(self.path / ('%s.vs' % self.filename)).st_mtime,
      os.stat(self.path / ('%s.fs' % self.filename)).st_mtime
    )
    if mtime == self.mtime:
      return
    self.destroyimpl(gl)
    self.createimpl(gl)

  def destroyimpl(self, gl):
    self.program.removeAllShaders()
    # self.program.destroy()
    self.program = None

  def enableimpl(self, gl, camera, shader):
    self.program.bind()

  def disableimpl(self, gl, camera, shader):
    self.program.release()
