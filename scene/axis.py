# axis.py: virtual axis object
#
# author: Antony Ducommun dit Boudry (nitro.tm@gmail.com)
# license: GPL
#

import numpy as np

from OpenGL import GL

from scene.mesh import Mesh, MeshVertexBuffer, MeshIndexBuffer


class Axis(Mesh):
  def __init__(self, scene, size=1.0, pointSize=3.0, lineWidth=1.0, color=(1.0, 1.0, 0.0), opacity=0.75):
    super(Axis, self).__init__(scene, pointSize, lineWidth)
    self.name = 'axis.%s' % id(self)

    vertexBuffer = MeshVertexBuffer(7)
    vertexBuffer.add(
      'vertex3',
      np.array(
        [
          [0,    0,    0   ],
          [0,    0,    0   ],
          [size, 0,    0   ],
          [0,    0,    0   ],
          [0,    size, 0   ],
          [0,    0,    0   ],
          [0,    0,    size],
        ],
        dtype=np.float32
      )
    )
    vertexBuffer.add(
      'color4',
      np.array(
        [
          [color[0], color[1], color[2], opacity],
          [1, 0, 0, opacity  ],
          [1, 0, 0, opacity/3],
          [0, 1, 0, opacity  ],
          [0, 1, 0, opacity/3],
          [0, 0, 1, opacity  ],
          [0, 0, 1, opacity/3],
        ],
        dtype=np.float32
      ),
      count=4
    )
    vertexBuffer.uniforms['colors'] = [4]

    if pointSize > 0:
      self.addDrawArrays('points', vertexBuffer, count=1, offset=0, primitives=GL.GL_POINTS, order=0)
    if lineWidth > 0:
      self.addDrawArrays('lines', vertexBuffer, count=6, offset=1, primitives=GL.GL_LINES, order=1)
