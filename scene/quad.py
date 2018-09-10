# quad.py: flat textured quad object
#
# author: Antony Ducommun dit Boudry (nitro.tm@gmail.com)
# license: GPL
#

import numpy as np

from OpenGL import GL

from scene.mesh import Mesh, MeshVertexBuffer, MeshIndexBuffer


class Quad(Mesh):
  def __init__(self, scene, size=2.0, pointSize=1.0, lineWidth=1.0, color=(1.0, 1.0, 1.0), opacity=1.0):
    super(Quad, self).__init__(scene, pointSize, lineWidth)
    self.name = 'quad.%s' % id(self)

    tx = ty = 0.001

    vertexBuffer = MeshVertexBuffer(4)
    vertexBuffer.add(
      'vertex3',
      np.array(
        [
          [-size/2, -size/2, 0],
          [-size/2,  size/2, 0],
          [ size/2,  size/2, 0],
          [ size/2, -size/2, 0]
        ],
        dtype=np.float32
      )
    )
    vertexBuffer.add(
      'color4',
      np.array(
        [ [color[0], color[1], color[2], opacity] for i in range(4) ],
        dtype=np.float32
      ),
      count=4
    )
    vertexBuffer.uniforms['colors'] = [4]
    vertexBuffer.add(
      'uv2',
      np.array(
        [
          [    tx, 1 - ty],
          [    tx,     ty],
          [1 - tx,     ty],
          [1 - tx, 1 - ty]
        ],
        dtype=np.float32
      ),
      count=2
    )

    self.addDrawArrays('quads', vertexBuffer, count=4, primitives=GL.GL_QUADS)
