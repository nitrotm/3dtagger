# scene.py: scene root and passes
#
# author: Antony Ducommun dit Boudry (nitro.tm@gmail.com)
# license: GPL
#

import array, json, time
import numpy as np

from OpenGL import GL

from scene.axis import Axis
from scene.box import BBox
from scene.camera import Camera, Ortho2DCamera, OrthoCamera, PerspectiveCamera, ViewCamera
from scene.mesh import Mesh
from scene.node import Node
from scene.plane import Plane
from scene.pointcloud import PointCloud
from scene.quad import Quad
from scene.shader import Shader
from scene.texture import Texture
from scene.util import ObjectProxy


class Scene(object):
  def __init__(self, clearcolor=(0.5, 0.5, 0.5, 1.0), gcinterval=5.0):
    self.gcinterval = gcinterval
    self.clearColor = clearcolor
    self.uniforms = dict()
    self.passes = dict()
    self.shaders = dict()
    self.removedShaders = list()
    self.textures = dict()
    self.removedTextures = list()
    self.nodes = dict()
    self.removedNodes = list()
    self.defaultCamera = ObjectProxy(Ortho2DCamera(self))
    self.defaultShader = ObjectProxy(self.getShader("display"))
    self.depthArray = None
    self.depthMap = np.array([])
    self.lastcleanup = time.time()


  def toJSON(self):
    return {
      'gcinterval': self.gcinterval,
      'clearColor': self.clearColor,
      'uniforms': self.uniforms,
      'passes': [ item.toJSON() for item in self.passes.values() ],
      'shaders': [ item.toJSON() for item in self.shaders.values() ],
      'removedShaders': [ item.toJSON() for item in self.removedShaders ],
      'textures': [ item.toJSON() for item in self.textures.values() ],
      'removedTextures': [ item.toJSON() for item in self.removedTextures ],
      'nodes': [ item.toJSON() for item in self.nodes.values() ],
      'removedNodes': [ item.toJSON() for item in self.removedNodes ],
      'defaultCamera': self.defaultCamera.toJSON(),
      'defaultShader': self.defaultShader.toJSON(),
    }

  def __repr__(self):
    return json.dumps(self.toJSON())

  def __str__(self):
    return json.dumps(self.toJSON(), indent='  ')


  def hasPass(self, name):
    return name in self.passes

  def addPass(self, name, camera=None, shader=None, order=0):
    if name in self.passes:
      raise Exception("pass name already exists")
    if not camera:
      camera = self.defaultCamera
    if not shader:
      shader = self.defaultShader
    item = ScenePass(self, name, camera, shader)
    item.order = order
    self.passes[name] = item
    return item

  def getPass(self, name):
    if name not in self.passes:
      raise Exception("pass name doesn't exist")
    return self.passes[name]

  def removePass(self, name):
    if name not in self.passes:
      raise Exception("pass name doesn't exist")
    self.passes[name].oncleanup()
    del self.passes[name]


  def getShader(self, filename):
    if filename in self.shaders:
      return self.shaders[filename]
    shader = Shader(self, filename)
    self.shaders[filename] = shader
    return shader

  def setDefaultShader(self, shader):
    self.defaultShader.apply(shader)


  def getTexture(self, filename):
    if filename in self.textures:
      return self.textures[filename]
    texture = Texture(self, filename)
    self.textures[filename] = texture
    return texture


  def hasNode(self, name):
    return name in self.nodes

  def addNode(self, node):
    if node.name in self.nodes:
      if self.nodes[node.name] != node:
        raise Exception("node name already exists")
    else:
      self.nodes[node.name] = node
    return node

  def getNode(self, name):
    if name not in self.nodes:
      raise Exception("node name doesn't exist")
    return self.nodes[name]

  def removeNode(self, name):
    if name not in self.nodes:
      raise Exception("node name doesn't exist")
    node = self.nodes[name]
    node.oncleanup()
    self.removedNodes.append(node)
    del self.nodes[name]

  def removeNodeByPrefix(self, prefix):
    remaining = dict()
    for (name, node) in self.nodes.items():
      if not name.startswith(prefix):
        remaining[name] = node
        continue
      node.oncleanup()
      self.removedNodes.append(node)
    self.nodes = remaining


  def getOrtho2DCamera(self, name, fov=1, near=-1, far=1, axisSize=0.25, pointSize=4.0, lineWidth=1.0, color=(1.0, 1.0, 0.0), opacity=0.75, order=0):
    if name in self.nodes:
      # TODO: update parameters?
      return self.nodes[name]
    node = Ortho2DCamera(self, fov, near, far, axisSize, pointSize, lineWidth, color, opacity)
    node.name = name
    node.order = order
    return self.addNode(node)

  def getOrthoCamera(self, name, hfov=50, near=-50, far=50, axisSize=0.25, pointSize=4.0, lineWidth=1.0, color=(1.0, 1.0, 0.0), opacity=0.75, order=0):
    if name in self.nodes:
      # TODO: update parameters?
      return self.nodes[name]
    node = OrthoCamera(self, hfov, near, far, axisSize, pointSize, lineWidth, color, opacity)
    node.name = name
    node.order = order
    return self.addNode(node)

  def getPerspectiveCamera(self, name, vfov=90, near=0.1, far=50.1, axisSize=0.25, pointSize=4.0, lineWidth=1.0, color=(1.0, 1.0, 0.0), opacity=0.75, order=0):
    if name in self.nodes:
      # TODO: update parameters?
      return self.nodes[name]
    node = PerspectiveCamera(self, vfov, near, far, axisSize, pointSize, lineWidth, color, opacity)
    node.name = name
    node.order = order
    return self.addNode(node)

  def getViewCamera(self, name, view=None, near=0.1, far=50.1, axisSize=0.25, pointSize=4.0, lineWidth=1.0, color=(1.0, 1.0, 0.0), opacity=0.75, order=0):
    if name in self.nodes:
      # TODO: update parameters?
      return self.nodes[name]
    if not view:
      raise Exception("view is required")
    node = ViewCamera(self, view, near, far, axisSize, pointSize, lineWidth, color, opacity)
    node.name = name
    node.order = order
    return self.addNode(node)

  def setDefaultCamera(self, camera):
    self.defaultCamera.apply(camera)


  def addAxis(self, name, size=1.0, pointSize=3.0, lineWidth=1.0, color=(1.0, 1.0, 0.0), opacity=0.75, order=0):
    node = Axis(self, size, pointSize, lineWidth, color, opacity)
    node.name = name
    node.order = order
    return self.addNode(node)

  def addMesh(self, name, pointSize=1.0, lineWidth=1.0, order=0):
    node = Mesh(self, pointSize, lineWidth)
    node.name = name
    node.order = order
    return self.addNode(node)

  def addPlane(self, name, size=25, pointSize=3.0, lineWidth=2.0, color=(0.0, 0.0, 0.0), opacity=1.0, order=0):
    node = Plane(self, size, pointSize, lineWidth, color, opacity)
    node.name = name
    node.order = order
    return self.addNode(node)

  def addPointCloud(self, name, pointSize=2.0, displayRatio=0.1, order=0):
    node = PointCloud(self, pointSize, displayRatio)
    node.name = name
    node.order = order
    return self.addNode(node)

  def addQuad(self, name, size=2.0, pointSize=1.0, lineWidth=1.0, color=(1.0, 1.0, 1.0), opacity=1.0, order=0):
    node = Quad(self, size, pointSize, lineWidth, color, opacity)
    node.name = name
    node.order = order
    return self.addNode(node)

  def addBBox(self, name, size=(1.0, 1.0, 1.0), lineWidth=1.0, color=(1.0, 1.0, 1.0), opacity=1.0, order=0):
    node = BBox(self, size, lineWidth, color, opacity)
    node.name = name
    node.order = order
    return self.addNode(node)


  def hasgarbage(self):
    for item in self.shaders.values():
      if item.hasgarbage():
        return True
    for item in self.textures.values():
      if item.hasgarbage():
        return True
    for item in self.nodes.values():
      if item.hasgarbage():
        return True
    if len(self.removedNodes) > 0:
      return True
    if len(self.removedShaders) > 0:
      return True
    if len(self.removedTextures) > 0:
      return True
    return False


  def destroy(self):
    self.removedShaders += list(self.shaders.values())
    self.removedTextures += list(self.textures.values())
    self.removedNodes += list(self.nodes.values())
    self.passes = dict()
    self.shaders = dict()
    self.textures = dict()
    self.nodes = dict()


  def depthmap(self, gl, width, height):
    if self.depthMap.size == 0:
      size = width * height
      if not self.depthArray or len(self.depthArray) < size:
        self.depthArray = array.array('f', [0 for i in range(size)])
      gl.glReadPixels(0, 0, width, height, GL.GL_DEPTH_COMPONENT, GL.GL_FLOAT, self.depthArray)
      self.depthMap = np.flip(
        np.array(self.depthArray[0:size], dtype=np.float32).reshape(height, width),
        0
      )
    return self.depthMap

  def depth(self, gl, x, y, width, height):
    return self.depthmap(gl, width, height)[y, x]

  def render(self, gl, width, height, uniforms=dict()):
    gl.glColorMask(GL.GL_TRUE, GL.GL_TRUE, GL.GL_TRUE, GL.GL_TRUE)
    gl.glDepthMask(GL.GL_TRUE)
    gl.glStencilMask(0xffffffff)

    gl.glClearColor(self.clearColor[0], self.clearColor[1], self.clearColor[2], self.clearColor[3])
    gl.glClearDepthf(1.0)
    gl.glClearStencil(0)
    gl.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT | GL.GL_STENCIL_BUFFER_BIT)

    uniforms.update(self.uniforms)

    depthChanged = False
    for item in sorted(self.passes.values(), key=lambda x: x.order):
      if item.onrender(gl, width, height, uniforms.copy()):
        depthChanged = True
    if depthChanged:
      self.depthMap = np.array([])

    if (time.time() - self.lastcleanup) > self.gcinterval:
      self.lastcleanup = time.time()
      self.oncleanup(gl)

  def oncleanup(self, gl):
    for item in self.shaders.values():
      if item.hasgarbage():
        item.ondestroy(gl)

    for item in self.textures.values():
      if item.hasgarbage():
        item.ondestroy(gl)

    for item in self.nodes.values():
      if item.hasgarbage():
        item.ondestroy(gl)

    if len(self.removedNodes) > 0:
      for item in self.removedNodes:
        item.oncleanup()
        item.ondestroy(gl)
      self.removedNodes = list()

    if len(self.removedShaders) > 0:
      for item in self.removedShaders:
        item.oncleanup()
        item.ondestroy(gl)
      self.removedShaders = list()

    if len(self.removedTextures) > 0:
      for item in self.removedTextures:
        item.oncleanup()
        item.ondestroy(gl)
      self.removedTextures = list()



class ScenePass(object):
  def __init__(self, scene, name, camera, shader):
    if not camera:
      raise Exception("camera is required")
    if not shader:
      raise Exception("shader is required")
    self.scene = scene
    self.name = name
    self.order = 0
    self.enabled = True
    self.colorMasks = (True, True, True, True)
    self.depthMask = True
    self.depthTest = True
    self.cullFace = True
    self.blend = True
    self.camera = camera
    self.shader = shader
    self.shader.onattach(self)
    self.uniforms = dict()
    self.nodes = dict()


  def toJSON(self):
    return {
      'name': self.name,
      'order': self.order,
      'enabled': self.enabled,
      'colorMasks': list(self.colorMasks),
      'depthMask': self.depthMask,
      'depthTest': self.depthTest,
      'cullFace': self.cullFace,
      'blend': self.blend,
      'camera': self.camera.name,
      'shader': self.shader.name,
      'uniforms': self.uniforms,
      'nodes': list(self.nodes.keys()),
    }

  def __repr__(self):
    return json.dumps(self.toJSON())

  def __str__(self):
    return json.dumps(self.toJSON(), indent='  ')


  def attachShader(self, shader):
    if not shader:
      raise Exception("shader is required")
    if self.shader:
      if self.shader == shader:
        return
      self.shader.ondetach(self)
    self.shader = shader
    self.shader.onattach(self)

  def detachShader(self, shader):
    if not self.shader or self.shader != shader:
      return
    self.shader.ondetach(self)
    self.shader = None

  def detachShaders(self):
    self.detachShader(self.shader)


  def attachNode(self, node):
    if node.name in self.nodes:
      if self.nodes[node.name] != node:
        raise Exception("node name already exists")
    else:
      self.nodes[node.name] = node
      node.onattachpass(self)

  def detachNode(self, node):
    if node.name not in self.nodes:
      raise Exception("node not attached to pass")
    node.ondetachpass(self)
    del self.nodes[node.name]

  def detachNodes(self):
    for node in self.nodes.values():
      node.ondetachpass(self)
    self.nodes = dict()


  def enable(self):
    self.enabled = True

  def disable(self):
    self.enabled = False

  def toggle(self):
    self.enabled = not self.enabled


  def onrender(self, gl, width, height, uniforms=dict()):
    if not self.enabled:
      return False

    gl.glColorMask(self.colorMasks[0], self.colorMasks[1], self.colorMasks[2], self.colorMasks[3])

    if self.depthMask:
      gl.glDepthMask(GL.GL_TRUE)
    else:
      gl.glDepthMask(GL.GL_FALSE)

    if self.depthTest:
      gl.glDepthFunc(GL.GL_LEQUAL)
      gl.glEnable(GL.GL_DEPTH_TEST)
    else:
      gl.glDepthFunc(GL.GL_ALWAYS)
      gl.glDisable(GL.GL_DEPTH_TEST)

    gl.glStencilMask(0)
    gl.glStencilFunc(GL.GL_NEVER, 0, 0xffffffff)
    gl.glStencilOp(GL.GL_KEEP, GL.GL_KEEP, GL.GL_KEEP)

    if self.cullFace:
      gl.glEnable(GL.GL_CULL_FACE)
    else:
      gl.glDisable(GL.GL_CULL_FACE)

    if self.blend:
      gl.glEnable(GL.GL_BLEND)
      gl.glBlendFunc(GL.GL_SRC_ALPHA, GL.GL_ONE_MINUS_SRC_ALPHA)
    else:
      gl.glDisable(GL.GL_BLEND)

    gl.glEnable(GL.GL_PROGRAM_POINT_SIZE)

    uniforms.update(self.uniforms)

    self.shader.enable(gl, self.camera, self.shader)

    self.camera.setup(gl, width, height, self.shader)

    depthChanged = self.camera.ismoved()
    for node in sorted(self.nodes.values(), key=lambda x: x.order):
      self.shader.setUniforms(uniforms)
      node.onrender(gl, self.camera, self.shader)
      depthChanged = node.ismoved() or depthChanged

    self.shader.disable(gl, self.camera, self.shader)

    return self.depthMask and depthChanged

  def oncleanup(self):
    self.detachShaders()
    self.detachNodes()
