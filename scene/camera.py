# camera.py: various camera object
#
# author: Antony Ducommun dit Boudry (nitro.tm@gmail.com)
# license: GPL
#

import array
import numpy as np

from PySide2.QtGui import QMatrix2x2, QMatrix3x3, QMatrix4x4, QQuaternion, QVector2D, QVector3D, QVector4D

from OpenGL import GL

from scene.axis import Axis
from scene.glu import norm, gluIdentity, gluTranslate3, gluRotate3, gluOrtho, gluPerpective, gluLookAt, gluProject, gluUnproject


class Camera(Axis):
  def __init__(self, scene, axisSize=0.25, pointSize=4.0, lineWidth=1.0, color=(1.0, 1.0, 0.0), opacity=0.75):
    super(Camera, self).__init__(scene, axisSize, pointSize, lineWidth, color, opacity)
    self.name = 'camera.%s' % id(self)
    self.changed = True
    self.width = -1
    self.height = -1
    self.projection = gluIdentity()
    self.modelView = gluIdentity()
    self.roll = self.pitch = self.yaw = 0
    self.eye = np.array([0, 0, 0], dtype=np.float64)
    self.front = np.array([0, 0, -1], dtype=np.float64)
    self.up = np.array([0, 1, 0], dtype=np.float64)
    self.atOrigin = True

  def toJSON(self):
    data = super(Camera, self).toJSON()
    data['projection'] = self.projection.tolist()
    data['modelview'] = self.modelView.tolist()
    data['eye'] = self.eye.tolist()
    data['front'] = self.front.tolist()
    data['up'] = self.up.tolist()
    data['atOrigin'] = self.atOrigin
    return data

  def load(self, config):
    self.mMatrix = np.array(config['mMatrix'], dtype=np.float64)
    self.projection = np.array(config['projection'], dtype=np.float64)
    self.modelView = np.array(config['modelView'], dtype=np.float64)
    self.roll = config['roll']
    self.pitch = config['pitch']
    self.yaw = config['yaw']
    self.eye = np.array(config['eye'], dtype=np.float64)
    self.front = np.array(config['front'], dtype=np.float64)
    self.up = np.array(config['up'], dtype=np.float64)
    self.atOrigin = config['origin']
    self.changed = True
    self.moved = True

  def save(self):
    return dict({
      'mMatrix': self.mMatrix.tolist(),
      'projection': self.projection.tolist(),
      'modelView': self.projection.tolist(),
      'roll': self.roll,
      'pitch': self.pitch,
      'yaw': self.yaw,
      'eye': self.eye.tolist(),
      'front': self.front.tolist(),
      'up': self.up.tolist(),
      'origin': self.atOrigin
    })

  def origin(self):
    super(Camera, self).origin()
    self.modelView = gluIdentity()
    self.roll = self.pitch = self.yaw = 0
    self.eye = np.array([0, 0, 0], dtype=np.float64)
    self.front = np.array([0, 0, -1], dtype=np.float64)
    self.up = np.array([0, 1, 0], dtype=np.float64)
    self.atOrigin = True
    self.changed = True
    self.moved = True

  def translate(self, tx=0, ty=0, tz=0):
    self.mMatrix = gluTranslate3(tx, ty, tz) @ self.mMatrix
    self.eye -= np.array([tx, ty, tz], dtype=np.float64)
    self.atOrigin = False
    self.changed = True
    self.moved = True

  def rotate(self, a=0, ax=0, ay=1, az=0):
    raise Exception('cameras cannot be rotated in world coordinates')

  def move(self, dx=0, dy=0, dz=0):
    rotation = gluRotate3(self.roll, 0, 0, 1)[0:3,0:3] @ gluRotate3(self.pitch, 1, 0, 0)[0:3,0:3] @ gluRotate3(self.yaw, 0, 1, 0)[0:3,0:3]
    translate = rotation.T @ np.array([dx, dy, dz], dtype=np.float64)
    self.mMatrix = gluTranslate3(translate[0], translate[1], translate[2]) @ self.mMatrix
    self.eye -= translate
    self.atOrigin = False
    self.changed = True
    self.moved = True

  def orient(self, dyaw=0, dpitch=0, droll=0):
    self.roll += droll
    self.pitch += dpitch
    self.yaw += dyaw
    self.mMatrix = self.mMatrix @ gluRotate3(-droll, 0, 0, 1) @ gluRotate3(-dpitch, 1, 0, 0) @ gluRotate3(-dyaw, 0, 1, 0)
    rotation = gluRotate3(self.roll, 0, 0, 1)[0:3,0:3] @ gluRotate3(self.pitch, 1, 0, 0)[0:3,0:3] @ gluRotate3(self.yaw, 0, 1, 0)[0:3,0:3]
    self.front = norm(rotation @ np.array([0, 0, -1], dtype=np.float64))
    self.up = norm(rotation @ np.array([0, 1, 0], dtype=np.float64))
    self.atOrigin = False
    self.changed = True
    self.moved = True

  def zoom(self, dfov):
    self.move(0, 0, dfov)

  def setup(self, gl, width, height, shader):
    self.update()

    gl.glViewport(0, 0, width, height)

    shader.setMatrix4x4('pMatrix', self.projection)
    shader.setMatrix4x4('vMatrix', self.modelView)
    shader.setVector3('cameraPosition', self.eye)

  def project(self, pt):
    self.update()
    pt = gluProject(pt, self.projection, self.modelView)
    return (
      pt[0] * (self.width - 1),
      pt[1] * (self.height - 1),
      pt[2],
      pt[3]
    )

  def unproject(self, x, y, z, w=1.0):
    self.update()
    pt = gluUnproject(
      [
        x / (self.width - 1),
        y / (self.height - 1),
        z,
        w
      ],
      self.projection,
      self.modelView
    )
    return pt

  def update(self):
    if not self.changed:
      return
    self.changed = False
    self.modelView = gluLookAt(self.eye, self.eye + self.front, self.up)


class Ortho2DCamera(Camera):
  def __init__(self, scene, fov=1, near=-1, far=1, axisSize=0.25, pointSize=4.0, lineWidth=1.0, color=(1.0, 1.0, 0.0), opacity=0.75):
    super(Ortho2DCamera, self).__init__(scene, axisSize, pointSize, lineWidth, color, opacity)
    self.fov = fov
    self.near = near
    self.far = far
    self.origin()

  def load(self, config):
    self.fov = config['fov']
    self.near = config['near']
    self.far = config['far']
    super(Ortho2DCamera, self).load(config)

  def save(self):
    config = super(Ortho2DCamera, self).save()
    config.update({
      'fov': self.fov,
      'near': self.near,
      'far': self.far
    })
    return config

  def zoom(self, dfov):
    self.fov = max(0.001, min(100, self.fov + dfov))
    self.changed = True
    self.moved = True

  def setup(self, gl, width, height, shader):
    if self.changed or self.width != width or self.height != height:
      self.width = width
      self.height = height
      a = height / width
      self.projection = gluOrtho(-self.fov, self.fov, -self.fov, self.fov, self.near, self.far)
      self.moved = True

    super(Ortho2DCamera, self).setup(gl, width, height, shader)


class OrthoCamera(Camera):
  def __init__(self, scene, hfov=50, near=-50, far=50, axisSize=0.25, pointSize=4.0, lineWidth=1.0, color=(1.0, 1.0, 0.0), opacity=0.75):
    super(OrthoCamera, self).__init__(scene, axisSize, pointSize, lineWidth, color, opacity)
    self.hfov = hfov
    self.near = near
    self.far = far
    self.origin()

  def load(self, config):
    self.hfov = config['hfov']
    self.near = config['near']
    self.far = config['far']
    super(OrthoCamera, self).load(config)

  def save(self):
    config = super(OrthoCamera, self).save()
    config.update({
      'hfov': self.hfov,
      'near': self.near,
      'far': self.far
    })
    return config

  def zoom(self, dfov):
    self.hfov = max(0.001, min(100, self.hfov + dfov))
    self.changed = True
    self.moved = True

  def setup(self, gl, width, height, shader):
    if self.changed or self.width != width or self.height != height:
      self.width = width
      self.height = height
      a = height / width
      self.projection = gluOrtho(-self.hfov, self.hfov, -self.hfov * a, self.hfov * a, self.near, self.far)
      self.moved = True

    super(OrthoCamera, self).setup(gl, width, height, shader)


class PerspectiveCamera(Camera):
  def __init__(self, scene, vfov=90, near=0.1, far=50.1, axisSize=0.25, pointSize=4.0, lineWidth=1.0, color=(1.0, 1.0, 0.0), opacity=0.75):
    super(PerspectiveCamera, self).__init__(scene, axisSize, pointSize, lineWidth, color, opacity)
    self.vfov = vfov
    self.near = near
    self.far = far
    self.origin()

  def load(self, config):
    self.vfov = config['vfov']
    self.near = config['near']
    self.far = config['far']
    super(PerspectiveCamera, self).load(config)

  def save(self):
    config = super(PerspectiveCamera, self).save()
    config.update({
      'vfov': self.vfov,
      'near': self.near,
      'far': self.far
    })
    return config

  def zoom(self, dfov):
    self.vfov = max(0.1, min(120, self.vfov + dfov))
    self.changed = True
    self.moved = True

  def setup(self, gl, width, height, shader):
    if self.changed or self.width != width or self.height != height:
      self.width = width
      self.height = height
      a = width / height
      self.projection = gluPerpective(self.vfov, a, self.near, self.far)
      self.moved = True

    super(PerspectiveCamera, self).setup(gl, width, height, shader)


class ViewCamera(Camera):
  def __init__(self, scene, view, near=0.1, far=50.1, axisSize=0.25, pointSize=4.0, lineWidth=1.0, color=(1.0, 1.0, 0.0), opacity=0.75):
    super(ViewCamera, self).__init__(scene, axisSize, pointSize, lineWidth, color, opacity)
    self.view = view
    self.near = near
    self.far = far
    self.origin()

  def load(self, config):
    self.near = config['near']
    self.far = config['far']
    super(ViewCamera, self).load(config)

  def save(self):
    config = super(ViewCamera, self).save()
    config.update({
      'near': self.near,
      'far': self.far
    })
    return config

  def origin(self):
    super(ViewCamera, self).origin()
    t = self.view.position()
    self.move(t[0], t[1], t[2])
    r = self.view.rotation[0:3,0:3].copy()
    r[1:3,:] = -r[1:3,:]
    euler = QQuaternion.fromRotationMatrix(QMatrix3x3(list(r.T.flat))).toEulerAngles()
    self.orient(-euler.y(), -euler.x(), -euler.z())
    self.atOrigin = True
    self.changed = True
    self.moved = True

  def setup(self, gl, width, height, shader):
    if self.changed or self.width != width or self.height != height:
      self.width = width
      self.height = height
      self.projection = self.view.intrinsic(width, height, self.near, self.far)
      self.moved = True

    super(ViewCamera, self).setup(gl, width, height, shader)
