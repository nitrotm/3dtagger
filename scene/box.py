# quad.py: flat textured quad object
#
# author: Antony Ducommun dit Boudry (nitro.tm@gmail.com)
# license: GPL
#

import numpy as np

from OpenGL import GL

from scene.mesh import Mesh, MeshVertexBuffer, MeshIndexBuffer


class BBox(Mesh):
  def __init__(self, scene, size=(1.0, 1.0, 1.0), lineWidth=1.0, color=(1.0, 1.0, 1.0), opacity=1.0):
    super(BBox, self).__init__(scene, 1.0, lineWidth)
    self.name = 'box.%s' % id(self)

    vertexBuffer = MeshVertexBuffer(8)
    vertexBuffer.add(
      'vertex3',
      np.array(
        [
          [-size[0]/2, -size[1]/2, -size[2]/2],
          [ size[0]/2, -size[1]/2, -size[2]/2],
          [ size[0]/2,  size[1]/2, -size[2]/2],
          [-size[0]/2,  size[1]/2, -size[2]/2],
          [-size[0]/2, -size[1]/2,  size[2]/2],
          [ size[0]/2, -size[1]/2,  size[2]/2],
          [ size[0]/2,  size[1]/2,  size[2]/2],
          [-size[0]/2,  size[1]/2,  size[2]/2],
        ],
        dtype=np.float32
      )
    )
    vertexBuffer.add(
      'color4',
      np.array(
        [ [color[0], color[1], color[2], opacity] for i in range(8) ],
        dtype=np.float32
      ),
      count=4
    )
    vertexBuffer.uniforms['colors'] = [4]

    indexBuffer = MeshIndexBuffer(
      elements=24,
      data=np.array(
        [
          0, 1, 1, 2, 2, 3, 3, 0,
          4, 5, 5, 6, 6, 7, 7, 4,
          0, 4, 1, 5, 2, 6, 3, 7,
        ],
        dtype=np.uint32
      ),
      primitives=GL.GL_LINES
    )

    self.addDrawElements('lines', vertexBuffer, indexBuffer)
