# scene.py: project mve scene container
#
# author: Antony Ducommun dit Boudry (nitro.tm@gmail.com)
# license: GPL
#

import io, math, sys, time

import numpy as np

from mve import MVEScene

from project.view import ProjectView


class ProjectScene(object):
  def __init__(self, project, name, path, views=dict()):
    self.project = project
    self.name = name
    self.path = path
    self.views = views
    self.mve = MVEScene(self.path)
    for item in self.mve.views.items:
      viewName = '%s:%04d' % (self.name, item.id)
      if item.id not in self.views:
        self.views[item.id] = ProjectView(self.project, viewName, item.id)
      view = self.views[item.id]
      view.name = viewName
      view.info = item
    for view in self.views.values():
      if not view.info:
        view.active = False
    self.renderPass = None


  def create(self):
    self.destroy()
    self.renderPass = self.project.renderer.addPass(self.name, order=10)
    self.cloudRenderPass = self.project.renderer.addPass(
      self.name + ':cloud',
      shader=self.project.cloudShader,
      order=11
    )

  def destroy(self):
    for item in self.views.values():
      item.destroy()
    if self.renderPass:
      self.project.renderer.removePass(self.renderPass.name)
      self.renderPass = None


  def select(self, clicks):
    changed = False
    for item in self.views.values():
      changed = item.select(clicks) or changed
    return changed
