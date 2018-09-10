# glu.py: opengl utilities
#
# author: Antony Ducommun dit Boudry (nitro.tm@gmail.com)
# license: GPL
#

import math
import numpy as np


def norm(v):
  return v / np.linalg.norm(v)

def gluIdentity():
  return np.eye(4, dtype=np.float64)

def gluTranslate(t):
  m = gluIdentity()
  m[0:3,3] = t
  return m

def gluTranslate3(tx, ty, tz):
  m = gluIdentity()
  m[0,3] = tx
  m[1,3] = ty
  m[2,3] = tz
  return m

def gluRotate3(a, rx, ry, rz):
  r = norm(np.array([rx, ry, rz]))
  c = math.cos(a * math.pi / 180)
  s = math.sin(a * math.pi / 180)
  m = gluIdentity()
  m[0,0] = (r[0]*r[0])*(1-c)+c
  m[0,1] = (r[0]*r[1])*(1-c)-r[2]*s
  m[0,2] = (r[0]*r[2])*(1-c)+r[1]*s
  m[1,0] = (r[1]*r[0])*(1-c)+r[2]*s
  m[1,1] = (r[1]*r[1])*(1-c)+c
  m[1,2] = (r[1]*r[2])*(1-c)-r[0]*s
  m[2,0] = (r[2]*r[0])*(1-c)-r[1]*s
  m[2,1] = (r[2]*r[1])*(1-c)+r[0]*s
  m[2,2] = (r[2]*r[2])*(1-c)+c
  return m

def gluOrtho(left, right, bottom, top, near=-1, far=1):
  p = gluIdentity()
  p[0,0] = 2 / (right - left)
  p[0,3] = -(right + left) / (right - left)
  p[1,1] = 2 / (top - bottom)
  p[1,3] = -(top + bottom) / (top - bottom)
  p[2,2] = 2 / (near - far)
  p[2,3] = -(far + near) / (far - near)
  return p

def gluPerpective(fy, a, near, far):
  f = math.atan((fy * math.pi / 180) / 2)
  p = np.zeros((4,4), dtype=np.float64)
  p[0,0] = f / a
  p[1,1] = f
  p[2,2] = (near + far) / (near - far)
  p[2,3] = 2 * near * far / (near - far)
  p[3,2] = -1
  return p

def gluLookAt(eye, center=[0, 0, 0], up=[0, 1, 0]):
  e = np.array(eye, dtype=np.float64)[0:3]
  c = np.array(center, dtype=np.float64)[0:3]
  u = norm(np.array(up, dtype=np.float64))[0:3]

  f = norm(c - e)
  s = np.cross(f, u)
  u = np.cross(s, f)

  v = gluIdentity()
  v[0:3,0] = s
  v[0:3,1] = u
  v[0:3,2] = -f
  return v @ gluTranslate(e)

def gluProject(pt, projection, modelView):
  pt = np.array(pt, dtype=np.float64)[0:4]
  v = projection @ (modelView @ pt)
  p = np.array(
    [
      ( v[0] / v[3] + 1) / 2,
      (-v[1] / v[3] + 1) / 2,
      ( v[2] / v[3] + 1) / 2,
      v[3]
    ],
    dtype=np.float64
  )
  return p

def gluUnproject(pt, projection, modelView):
  pt = np.array(pt, dtype=np.float64)[0:4]
  p = np.linalg.inv(projection @ modelView) @ np.array(
    [
       (2 * pt[0] - 1),
      -(2 * pt[1] - 1),
       (2 * pt[2] - 1),
      pt[3]
    ],
    dtype=np.float64
  )
  p[0:3] /= p[3]
  p[3] = 1.0
  return p
