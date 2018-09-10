# node.py: base renderable scene node
#
# author: Antony Ducommun dit Boudry (nitro.tm@gmail.com)
# license: GPL
#

import array, json, time

from OpenGL import GL

from scene.glu import gluIdentity, gluTranslate3, gluRotate3


class Node(object):
  def __init__(self, scene, name):
    self.scene = scene
    self.name = name
    self.order = 0
    self.visible = True
    self.created = False
    self.mMatrix = gluIdentity()
    self.moved = True
    self.uniforms = dict()
    self.uniforms["colors"] = [0]
    self.uniforms['pointSize'] = [1.0, 0.0]
    self.uniforms["hasTexture"] = [False]
    self.passes = dict()
    self.texture = None

  def toJSON(self):
    return {
      'name': self.name,
      'order': self.order,
      'visible': self.visible,
      'created': self.created,
      'mMatrix': self.mMatrix.tolist(),
      'uniforms': self.uniforms,
      'passes': list(self.passes.keys()),
      'texture': self.texture.toJSON() if self.texture else None,
    }

  def __repr__(self):
    return json.dumps(self.toJSON())

  def __str__(self):
    return json.dumps(self.toJSON(), indent='  ')


  def attachTexture(self, texture):
    if not texture:
      raise Exception("texture is required")
    if self.texture:
      if self.texture == texture:
        return
      self.texture.ondetach(self)
    self.texture = texture
    self.texture.onattach(self)
    self.uniforms["hasTexture"] = [True]

  def detachTexture(self, texture):
    if not self.texture or self.texture != texture:
      return
    self.texture.ondetach(self)
    self.texture = None
    self.uniforms["hasTexture"] = [False]

  def detachTextures(self):
    self.detachTexture(self.texture)


  def show(self):
    self.visible = True

  def hide(self):
    self.visible = False

  def toggle(self):
    self.visible = not self.visible


  def ismoved(self):
    if self.moved:
      self.moved = False
      return True
    return False

  def origin(self):
    self.mMatrix = gluIdentity()
    self.moved = True

  def translate(self, tx=0, ty=0, tz=0):
    self.mMatrix = gluTranslate3(tx, ty, tz) @ self.mMatrix
    self.moved = True

  def rotate(self, a=0, ax=0, ay=1, az=0):
    self.mMatrix = gluRotate3(a, ax, ay, az) @ self.mMatrix
    self.moved = True


  def oncreate(self, gl):
    if not self.created:
      self.createimpl(gl)
      self.created = True
      # print("node %s created" % self.name)

  def ondestroy(self, gl):
    if len(self.passes) > 0:
      raise Exception("node is attached: %s" % [ item.name for item in self.passes ])
    if self.created:
      self.destroyimpl(gl)
      self.created = False
      # print("node %s destroyed" % self.name)


  def onrender(self, gl, camera, shader):
    if not self.visible:
      return False
    if not self.created:
      self.oncreate(gl)

    vmMatrix = camera.modelView @ self.mMatrix
    shader.setUniforms(self.uniforms)
    shader.setMatrix4x4('mMatrix', self.mMatrix)
    shader.setMatrix4x4('vmMatrix', vmMatrix)
    shader.setMatrix4x4('pvmMatrix', camera.projection @ vmMatrix)

    self.onrenderinternal(gl, camera, shader)
    return True

  def onrenderinternal(self, gl, camera, shader):
    if self.texture:
      self.texture.enable(gl, camera, shader)

    if self.prerenderimpl(gl, camera, shader):
      self.renderimpl(gl, camera, shader)
    self.postrenderimpl(gl, camera, shader)

    if self.texture:
      self.texture.disable(gl, camera, shader)


  def hasgarbage(self):
    return self.created and len(self.passes) == 0

  def onattachpass(self, item):
    self.passes[item.name] = item

  def ondetachpass(self, item):
    del self.passes[item.name]

  def oncleanup(self):
    self.detachTextures()
    for item in list(self.passes.values()):
      item.detachNode(self)


  def createimpl(self, gl):
    pass

  def destroyimpl(self, gl):
    pass

  def prerenderimpl(self, gl, camera, shader):
    return True

  def renderimpl(self, gl, camera, shader):
    pass

  def postrenderimpl(self, gl, camera, shader):
    pass
