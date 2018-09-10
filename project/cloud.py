# cloud.py: project point cloud data container
#
# author: Antony Ducommun dit Boudry (nitro.tm@gmail.com)
# license: GPL
#

import io, math, sys, time

import numpy as np


class ProjectCloud(object):
  def __init__(self, count=0, vertices=np.array((3,), dtype=np.float32), colors=np.array((4,), dtype=np.float32)):
    self.count = count
    self.vertices = vertices
    self.colors = colors
    self.buildbbox()


  def load(self, ply):
    self.count = ply['vertex'].count
    indices = np.random.permutation(np.arange(0, self.count, dtype=np.uint32))
    self.vertices = np.column_stack(
      (
        ply['vertex'].data['x'].astype(np.float32, copy=False),
        ply['vertex'].data['y'].astype(np.float32, copy=False),
        ply['vertex'].data['z'].astype(np.float32, copy=False)
      )
    )[indices,:]
    self.colors = np.column_stack(
      (
        ply['vertex'].data['red'].astype(np.uint8, copy=False),
        ply['vertex'].data['green'].astype(np.uint8, copy=False),
        ply['vertex'].data['blue'].astype(np.uint8, copy=False),
        (ply['vertex'].data['confidence'] * 255.0).astype(np.uint8, copy=False)
      )
    )[indices,:]
    self.buildbbox()

  def unload(self):
    self.count = 0
    self.vertices = np.array((0,3), dtype=np.float32)
    self.colors = np.array((0,4), dtype=np.float32)

  def buildbbox(self):
    self.bbox1 = np.amin(self.vertices, axis=0)
    self.bbox2 = np.amax(self.vertices, axis=0)
    return (self.bbox1, self.bbox2)
