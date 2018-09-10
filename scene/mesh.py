# pointcloud.py: point cloud object loaded from ply file
#
# author: Antony Ducommun dit Boudry (nitro.tm@gmail.com)
# license: GPL
#

import array, ctypes, math
import numpy as np
import scipy.spatial as sp

from OpenGL import GL

from PySide2.QtGui import QOpenGLBuffer, QOpenGLVertexArrayObject

from shiboken2 import VoidPtr

from plyfile import PlyData

from scene.node import Node


class Mesh(Node):
  def __init__(self, scene, pointSize=1.0, lineWidth=1.0):
    super(Mesh, self).__init__(scene, 'mesh.%s' % id(self))
    self.pointSize = pointSize
    self.lineWidth = lineWidth
    self.commands = dict()
    self.removedCommands = list()


  def addDrawArrays(self, name, vertexBuffer=None, count=0, offset=0, primitives=GL.GL_POINTS, order=0):
    if not vertexBuffer:
      vertexBuffer = MeshVertexBuffer()
    command = MeshDrawArrays(vertexBuffer, count, offset, primitives)
    command.name = name
    command.order = order
    return self.addCommand(command)

  def addDrawElements(self, name, vertexBuffer=None, indexBuffer=None, offset=0, count=-1, order=0):
    if not vertexBuffer:
      vertexBuffer = MeshVertexBuffer()
    if not indexBuffer:
      indexBuffer = MeshIndexBuffer()
    command = MeshDrawElements(vertexBuffer, indexBuffer, offset, count)
    command.name = name
    command.order = order
    return self.addCommand(command)


  def addCommand(self, command):
    if command.name in self.commands:
      if self.commands[command.name] != command:
        raise Exception("command name already exist")
    else:
      self.commands[command.name] = command
    return command

  def getCommand(self, name):
    if name not in self.commands:
      raise Exception("command name doesn't exist")
    return self.commands[name]

  def removeCommand(self, name):
    if name not in self.commands:
      raise Exception("command name doesn't exist")
    command = self.commands[name]
    self.removedCommands.add(command)
    del self.commands[name]


  def createimpl(self, gl):
    for command in self.commands.values():
      command.oncreate(gl)

  def destroyimpl(self, gl):
    for command in self.commands.values():
      command.ondestroy(gl)
    if len(self.removedCommands) > 0:
      for item in self.removedCommands:
        item.ondestroy(gl)
      self.removedCommands = list()

  def prerenderimpl(self, gl, camera, shader):
    gl.glLineWidth(self.lineWidth)
    return True

  def renderimpl(self, gl, camera, shader):
    for command in sorted(self.commands.values(), key=lambda x: x.order):
      shader.setValues("pointSize", self.pointSize, 0.0)
      command.onrender(gl, camera, shader)
    if len(self.removedCommands) > 0:
      for item in self.removedCommands:
        item.ondestroy(gl)
      self.removedCommands = list()


class MeshDrawCommand(object):
  def __init__(self, vertexBuffer, offset=0, count=0, order=0):
    self.name = 'draw.%s' % id(self)
    self.vertexBuffer = vertexBuffer
    self.extraVertexBuffers = []
    self.offset = offset
    self.count = count
    self.order = order
    self.uniforms = dict()
    self.enabled = True

  def oncreate(self, gl):
    self.vertexBuffer.create(gl)
    for vertexBuffer in self.extraVertexBuffers:
      vertexBuffer.create(gl)

  def ondestroy(self, gl):
    self.vertexBuffer.destroy(gl)
    for vertexBuffer in self.extraVertexBuffers:
      vertexBuffer.destroy(gl)

  def onrender(self, gl, camera, shader):
    if not self.enabled:
      return

    shader.setUniforms(self.uniforms)

    self.vertexBuffer.enable(gl, shader)
    for vertexBuffer in self.extraVertexBuffers:
      vertexBuffer.enable(gl, shader)

    self.onrenderimpl(gl, camera, shader)

    self.vertexBuffer.disable(gl, shader)
    for vertexBuffer in self.extraVertexBuffers:
      vertexBuffer.disable(gl, shader)

  def onrenderimpl(self, gl, camera, shader):
    pass


class MeshDrawArrays(MeshDrawCommand):
  def __init__(self, vertexBuffer, count, offset=0, primitives=GL.GL_POINTS):
    super(MeshDrawArrays, self).__init__(vertexBuffer, offset, count)
    self.primitives = primitives

  def onrenderimpl(self, gl, camera, shader):
    elements = min(self.count, self.vertexBuffer.vertices - self.offset)
    if elements > 0:
      gl.glDrawArrays(self.primitives, self.offset, elements)


class MeshDrawElements(MeshDrawCommand):
  def __init__(self, vertexBuffer, indexBuffer, offset=0, count=-1):
    super(MeshDrawElements, self).__init__(vertexBuffer, offset, count)
    self.indexBuffer = indexBuffer

  def oncreate(self, gl):
    super(MeshDrawElements, self).oncreate(gl)
    self.indexBuffer.create(gl)

  def ondestroy(self, gl):
    self.indexBuffer.destroy(gl)
    super(MeshDrawElements, self).ondestroy(gl)

  def onrenderimpl(self, gl, camera, shader):
    elements = self.indexBuffer.elements - self.offset
    if self.count >= 0:
      elements = min(self.count, elements)
    if elements > 0:
      self.indexBuffer.enable(gl, shader)
      gl.glDrawElements(
        self.indexBuffer.primitives,
        elements,
        self.indexBuffer.datatype,
        VoidPtr(self.offset * self.indexBuffer.datasize)
      )
      self.indexBuffer.disable(gl, shader)


class MeshVertexBuffer(object):
  def __init__(self, vertices=0):
    self.update(vertices)
    self.uniforms = dict()
    self.buffer = None

  def update(self, vertices):
    self.vertices = vertices
    self.attributes = dict()
    self.offsets = dict()
    self.size = 0
    self.changed = True

  def add(self, name, data, count=3, datatype=GL.GL_FLOAT):
    self.attributes[name] = MeshVertexAttribute(name, data, count, datatype)
    self.changed = True

  def remove(self, name):
    if name in self.attributes:
      del self.attributes[name]
      self.changed = True

  def create(self, gl):
    if not self.buffer:
      self.buffer = QOpenGLBuffer(QOpenGLBuffer.VertexBuffer)
    if not self.buffer.isCreated() and not self.buffer.create():
      raise Exception("buffer creation failed!")
    self.buffer.bind()
    self.offsets = dict()
    self.size = 0
    for item in self.attributes.values():
      self.offsets[item.name] = self.size
      self.size += self.vertices * item.count * item.datasize
    self.buffer.allocate(self.size)
    for item in self.attributes.values():
      self.buffer.write(self.offsets[item.name], item.data.data, self.vertices * item.count * item.datasize)
    self.buffer.release()
    self.changed = False

  def destroy(self, gl):
    if not self.buffer:
      return
    self.buffer.destroy()
    self.buffer = None
    self.changed = True

  def enable(self, gl, shader):
    if self.changed:
      self.create(gl)
    shader.setUniforms(self.uniforms)
    self.buffer.bind()
    for item in self.attributes.values():
      if item.enabled:
        shader.setAttributeArray(item.name, item.datatype, self.offsets[item.name], item.count)
    self.buffer.release()

  def disable(self, gl, shader):
    for item in self.attributes.values():
      if item.enabled:
        shader.unsetAttributeArray(item.name)


class MeshIndexBuffer(object):
  def __init__(self, elements=0, data=np.zeros((0), dtype=np.uint32), primitives=GL.GL_POINTS, datatype=GL.GL_UNSIGNED_INT):
    self.update(elements, data, primitives, datatype)
    self.uniforms = dict()
    self.buffer = None

  def update(self, elements, data, primitives=GL.GL_POINTS, datatype=GL.GL_UNSIGNED_INT):
    self.elements = elements
    self.data = data
    self.primitives = primitives
    self.datatype = datatype
    if datatype == GL.GL_UNSIGNED_BYTE:
      self.datasize = 1
    elif datatype == GL.GL_UNSIGNED_SHORT:
      self.datasize = 2
    elif datatype == GL.GL_UNSIGNED_INT:
      self.datasize = 4
    else:
      raise Exception("unsupported index type")
    self.size = 0
    self.changed = True

  def create(self, gl):
    if not self.buffer:
      self.buffer = QOpenGLBuffer(QOpenGLBuffer.IndexBuffer)
    if not self.buffer.isCreated() and not self.buffer.create():
      raise Exception("buffer creation failed!")
    self.buffer.bind()
    self.size = self.elements * self.datasize
    self.buffer.allocate(self.size)
    self.buffer.write(0, self.data.data, self.elements * self.datasize)
    self.buffer.release()
    self.changed = False

  def destroy(self, gl):
    if not self.buffer:
      return
    self.buffer.destroy()
    self.buffer = None
    self.changed = True

  def enable(self, gl, shader):
    if self.changed:
      self.create(gl)
    shader.setUniforms(self.uniforms)
    self.buffer.bind()

  def disable(self, gl, shader):
    self.buffer.release()


class MeshVertexAttribute(object):
  def __init__(self, name, data, count=3, datatype=GL.GL_FLOAT):
    self.name = name
    self.data = data
    self.count = count
    self.datatype = datatype
    if datatype == GL.GL_BYTE or datatype == GL.GL_UNSIGNED_BYTE:
      self.datasize = 1
    elif datatype == GL.GL_SHORT or datatype == GL.GL_UNSIGNED_SHORT:
      self.datasize = 2
    elif datatype == GL.GL_INT or datatype == GL.GL_UNSIGNED_INT:
      self.datasize = 4
    elif datatype == GL.GL_FLOAT:
      self.datasize = 4
    elif datatype == GL.GL_DOUBLE:
      self.datasize = 8
    else:
      raise Exception("unsupported attribute type")
    self.enabled = True


def loadMeshVertexBufferPly(ply, vertexBuffer, colors='rgb', normals=False, uvs=False):
  print("reading ply (%d verts)..." % ply['vertex'].count)

  vertexBuffer.update(ply['vertex'].count)
  vertexBuffer.add(
    'vertex3',
    np.column_stack(
      (
        np.array(ply['vertex'].data['x'], dtype=np.float32),
        np.array(ply['vertex'].data['y'], dtype=np.float32),
        np.array(ply['vertex'].data['z'], dtype=np.float32)
      )
    )
  )

  if colors == 'rgba':
    vertexBuffer.add(
      'color4',
      np.column_stack(
        (
          np.array(ply['vertex'].data['red'],   dtype=np.float32),
          np.array(ply['vertex'].data['green'], dtype=np.float32),
          np.array(ply['vertex'].data['blue'],  dtype=np.float32),
          np.array(ply['vertex'].data['alpha'], dtype=np.float32)
        )
      ) / 255.0,
      count=4
    )
    vertexBuffer.uniforms['colors'] = [4]
  elif colors == 'rgbc':
    vertexBuffer.add(
      'color4',
      np.column_stack(
        (
          np.array(ply['vertex'].data['red'],        dtype=np.float32) / 255.0,
          np.array(ply['vertex'].data['green'],      dtype=np.float32) / 255.0,
          np.array(ply['vertex'].data['blue'],       dtype=np.float32) / 255.0,
          np.array(ply['vertex'].data['confidence'], dtype=np.float32)
        )
      ),
      count=4
    )
    vertexBuffer.uniforms['colors'] = [4]
  elif colors == 'rgb':
    vertexBuffer.add(
      'color3',
      np.column_stack(
        (
          np.array(ply['vertex'].data['red'],   dtype=np.float32),
          np.array(ply['vertex'].data['green'], dtype=np.float32),
          np.array(ply['vertex'].data['blue'],  dtype=np.float32)
        )
      ) / 255.0
    )
    vertexBuffer.uniforms['colors'] = [3]
  else:
    vertexBuffer.uniforms['colors'] = [0]

  if normals:
    vertexBuffer.add(
      'normal3',
      np.column_stack(
        (
          np.array(ply['vertex'].data['nx'], dtype=np.float32),
          np.array(ply['vertex'].data['ny'], dtype=np.float32),
          np.array(ply['vertex'].data['nz'], dtype=np.float32)
        )
      )
    )

  if uvs:
    vertexBuffer.add(
      'uv2',
      np.column_stack(
        (
          np.array(ply['vertex'].data['u'], dtype=np.float32),
          np.array(ply['vertex'].data['v'], dtype=np.float32)
        )
      ),
      count=2
    )


def loadMeshIndexBufferPly(ply, indexBuffer):
  print('reading faces (%d)...' % ply['face'].count)
  indexBuffer.update(
    ply['face'].count * 3,
    np.array(ply['face'].data['vertex_indices'], dtype=np.uint32).flat,
    GL.GL_TRIANGLES
  )
  return

def loadMeshDrawElementsPly(file, vertexBuffer, indexBuffer, colors='rgb', normals=False, uvs=False, indices=False):
  ply = PlyData.read(file)
  loadMeshVertexBufferPly(ply, vertexBuffer, colors, normals, uvs)
  if indices:
    loadMeshIndexBufferPly(ply, indexBuffer)
  else:
    indexBuffer.update(
      ply['vertex'].count,
      np.random.permutation(np.arange(0, ply['vertex'].count, dtype=np.uint32)),
      GL.GL_POINTS
    )

def MeshDrawArraysPly(file, colors='rgb', normals=False, uvs=False):
  ply = PlyData.read(file)
  vertexBuffer = MeshVertexBuffer()
  loadMeshVertexBufferPly(ply, vertexBuffer, colors, normals, uvs)
  return MeshDrawArrays(vertexBuffer, ply['vertex'].count)

def MeshDrawElementsPly(file, colors='rgb', normals=False, uvs=False, indices=False):
  vertexBuffer = MeshVertexBuffer()
  indexBuffer = MeshIndexBuffer()
  loadMeshDrawElementsPly(file, vertexBuffer, indexBuffer, colors, normals, uvs, indices)
  return MeshDrawElements(vertexBuffer, indexBuffer)
