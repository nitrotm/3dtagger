# scene.py: scene state
#
# author: Antony Ducommun dit Boudry (nitro.tm@gmail.com)
# license: GPL
#

import array, json, time
import numpy as np

from OpenGL import GL


class SceneState(object):
  def __init__(self, scene, name):
    self.scene = scene
    self.name = name
    self.created = False
    self.enabled = 0
    self.deps = set()


  def toJSON(self):
    return {
      'name': self.name,
      'created': self.created,
      'deps': [ item.name for item in self.deps ],
    }

  def __repr__(self):
    return json.dumps(self.toJSON())

  def __str__(self):
    return json.dumps(self.toJSON(), indent='  ')


  def enable(self, gl, camera, shader):
    if not self.created:
      self.oncreate(gl)
    if self.enabled < 0:
      raise Exception("invalid enable count")
    if self.enabled == 0:
      self.updateimpl(gl)
      self.enableimpl(gl, camera, shader)
    self.enabled += 1

  def disable(self, gl, camera, shader):
    if not self.created:
      self.oncreate(gl)
    if self.enabled <= 0:
      raise Exception("invalid enable count")
    self.enabled -= 1
    if self.enabled == 0:
      self.disableimpl(gl, camera, shader)


  def oncreate(self, gl):
    if not self.created:
      self.createimpl(gl)
      self.created = True
      self.enabled = 0
      # print("state %s created" % self.name)

  def ondestroy(self, gl):
    if self.enabled > 0:
      raise Exception("state is enabled")
    if len(self.deps) > 0:
      raise Exception("state is attached: %s" % [ item.name for item in self.deps ])
    if self.created:
      self.destroyimpl(gl)
      self.created = False
      self.enabled = 0
      # print("state %s destroyed" % self.name)


  def hasgarbage(self):
    return self.created and len(self.deps) == 0

  def onattach(self, item):
    self.deps.add(item)

  def ondetach(self, item):
    if item not in self.deps:
      return
    self.deps.remove(item)

  def oncleanup(self):
    self.deps = set()


  def createimpl(self, gl):
    pass

  def updateimpl(self, gl):
    pass

  def destroyimpl(self, gl):
    pass

  def enableimpl(self, gl, camera, shader):
    pass

  def disableimpl(self, gl, camera, shader):
    pass
