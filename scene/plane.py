# plane.py: virtual plane object
#
# author: Antony Ducommun dit Boudry (nitro.tm@gmail.com)
# license: GPL
#

import numpy as np

from OpenGL import GL

from scene.mesh import Mesh, MeshVertexBuffer, MeshDrawArrays


class Plane(Mesh):
  def __init__(self, scene, size=25, pointSize=3.0, lineWidth=2.0, color=(0.0, 0.0, 0.0), opacity=1.0):
    super(Plane, self).__init__(scene, pointSize, lineWidth)
    self.name = 'plane.%s' % id(self)

    i = 0
    n = (2*size + 1)**2
    points = np.zeros((n, 3), dtype=np.float32)
    for x in range(-size, size+1):
      for z in range(-size, size+1):
        points[i,:] = [x, 0, z]
        i += 1
    vertexBuffer1 = MeshVertexBuffer(n)
    vertexBuffer1.add('vertex3', points)
    vertexBuffer1.add(
      'color4',
      np.array(
        [ [color[0], color[1], color[2], opacity] for i in range(n) ],
        dtype=np.float32
      ),
      count=4
    )
    vertexBuffer1.uniforms['colors'] = [4]

    vertexBuffer2 = MeshVertexBuffer(8)
    vertexBuffer2.add(
      'vertex3',
      np.array(
        [
          [-size, 0, -size],
          [ size, 0, -size],
          [-size, 0,  size],
          [ size, 0,  size],
          [-size, 0, -size],
          [-size, 0,  size],
          [ size, 0, -size],
          [ size, 0,  size]
        ],
        dtype=np.float32
      )
    )
    vertexBuffer2.add(
      'color4',
      np.array(
        [ [color[0], color[1], color[2], opacity] for i in range(8) ],
        dtype=np.float32
      ),
      count=4
    )
    vertexBuffer2.uniforms['colors'] = [4]

    self.addDrawArrays('points', vertexBuffer1, count=n, offset=0, primitives=GL.GL_POINTS, order=0)
    self.addDrawArrays('lines', vertexBuffer2, count=8, offset=0, primitives=GL.GL_LINES, order=1)
