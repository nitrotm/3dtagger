# texture.py: opengl texture state
#
# author: Antony Ducommun dit Boudry (nitro.tm@gmail.com)
# license: GPL
#

from OpenGL import GL

from PySide2.QtGui import QImage, QOpenGLTexture

from scene.state import SceneState


class Texture(SceneState):
  def __init__(self, scene, filename):
    super(Texture, self).__init__(scene, filename)
    self.filename = filename
    self.texture = None
    self.width = 0
    self.height = 0


  def toJSON(self):
    data = super(Texture, self).toJSON()
    data['filename'] = self.filename
    return data


  def oncleanup(self):
    for item in list(self.deps):
      item.detachTexture(self)
    super(Texture, self).oncleanup()


  def createimpl(self, gl):
    self.texture = QOpenGLTexture(QImage(self.filename))
    self.width = self.texture.width()
    self.height = self.texture.height()

  def destroyimpl(self, gl):
    self.texture.destroy()
    self.texture = None
    self.width = 0
    self.height = 0

  def enableimpl(self, gl, camera, shader):
    self.texture.bind()

  def disableimpl(self, gl, camera, shader):
    self.texture.release()
