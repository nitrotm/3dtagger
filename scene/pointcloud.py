# pointcloud.py: point cloud object loaded from ply file
#
# author: Antony Ducommun dit Boudry (nitro.tm@gmail.com)
# license: GPL
#

import array, io, lzma, math
import numpy as np
import scipy.spatial as sp

from OpenGL import GL

from PySide2.QtGui import QOpenGLBuffer

from scene.mesh import Mesh, MeshVertexBuffer, MeshIndexBuffer


class PointCloud(Mesh):
  def __init__(self, scene, pointSize=1.0, displayRatio=1.0):
    super(PointCloud, self).__init__(scene, pointSize)
    self.displayRatio = displayRatio

    self.selection = MeshVertexBuffer()

    self.points = self.addDrawArrays('points', MeshVertexBuffer())
    # self.points = self.addDrawElements('points', MeshVertexBuffer(), MeshIndexBuffer())
    self.points.extraVertexBuffers.append(self.selection)
    self.points.enabled = False


  def setData(self, count, vertices, colors=np.array((0,))):
    self.points.vertexBuffer.update(count)
    # self.points.indexBuffer.update(count, np.random.permutation(np.arange(0, count, dtype=np.uint32)))
    if vertices.shape[0] == count and vertices.shape[1] == 3:
      self.points.vertexBuffer.add('vertex3', vertices)
    else:
      raise Exception("invalid vertex shape")
    if colors.shape[0] > 0:
      if colors.shape[0] == count and colors.shape[1] == 3:
        self.points.vertexBuffer.add('color3', colors, datatype=GL.GL_UNSIGNED_BYTE)
        self.points.vertexBuffer.uniforms['colors'] = [3]
      elif colors.shape[0] == count and colors.shape[1] == 4:
        self.points.vertexBuffer.add('color4', colors, count=4, datatype=GL.GL_UNSIGNED_BYTE)
        self.points.vertexBuffer.uniforms['colors'] = [4]
      else:
        raise Exception("invalid color shape")
    else:
      self.points.vertexBuffer.uniforms['colors'] = [0]
    self.points.enabled = count > 0

    self.selection.update(count)
    self.selection.add('selection', np.zeros((count), dtype=np.uint8), count=1, datatype=GL.GL_UNSIGNED_BYTE)


  def updateSelection(self, indices, include):
    changed = False
    if include:
      for index in indices:
        if self.selection.attributes['selection'].data[index]:
          continue
        self.selection.attributes['selection'].data[index] = 1
        changed = True
    else:
      for index in indices:
        if not self.selection.attributes['selection'].data[index]:
          continue
        self.selection.attributes['selection'].data[index] = 0
        changed = True
    if changed:
      self.selection.changed = True
    return changed

  def clearSelection(self):
    self.selection.attributes['selection'].data *= 0
    self.selection.changed = True


  def prerenderimpl(self, gl, camera, shader):
    self.points.count = math.ceil(self.points.vertexBuffer.vertices * self.displayRatio)
    self.points.uniforms['pointSize'] = [
      self.pointSize + math.log(1 / min(1, max(0.25, self.displayRatio))),
      0.0
    ]
    return super(PointCloud, self).prerenderimpl(gl, camera, shader)
