# mve.py: mve scene loader
#
# see https://www.gcc.tu-darmstadt.de/home/proj/mve/
#
# author: Antony Ducommun dit Boudry (nitro.tm@gmail.com)
# license: GPL
#

import cv2, json, math, struct
import numpy as np

from configparser import ConfigParser
from pathlib import Path, PurePath

from PIL import Image


IMAGE_TYPE_UNKNOWN  = 0
IMAGE_TYPE_UINT8    = 1
IMAGE_TYPE_UINT16   = 2
IMAGE_TYPE_UINT32   = 3
IMAGE_TYPE_UINT64   = 4
IMAGE_TYPE_SINT8    = 5
IMAGE_TYPE_SINT16   = 6
IMAGE_TYPE_SINT32   = 7
IMAGE_TYPE_SINT64   = 8
IMAGE_TYPE_FLOAT    = 9
IMAGE_TYPE_DOUBLE   = 10


def readmveiheaders(path):
  with Path(path).open('rb') as f:
    # read mvei signature
    signature = f.read(11)
    if signature != b"\211MVE_IMAGE\n":
      raise Exception('Invalid mvei header: %s' % path)

    # read mvei header
    header = f.read(4*4)
    (width, height, channels, rawtype) = struct.unpack('=IIII', header)

    # convert datatype to numpy
    if rawtype == IMAGE_TYPE_UINT8:
      dtype = np.uint8
    elif rawtype == IMAGE_TYPE_UINT16:
      dtype = np.uint16
    elif rawtype == IMAGE_TYPE_UINT32:
      dtype = np.uint32
    elif rawtype == IMAGE_TYPE_UINT64:
      dtype = np.uint64
    elif rawtype == IMAGE_TYPE_SINT8:
      dtype = np.int8
    elif rawtype == IMAGE_TYPE_SINT16:
      dtype = np.int16
    elif rawtype == IMAGE_TYPE_SINT32:
      dtype = np.int32
    elif rawtype == IMAGE_TYPE_SINT64:
      dtype = np.int64
    elif rawtype == IMAGE_TYPE_FLOAT:
      dtype = np.float32
    elif rawtype == IMAGE_TYPE_DOUBLE:
      dtype = np.float64
    else:
      raise Exception('Unsupported mvei format (%d): %s' % (rawtype, path))
    return (width, height, channels, dtype)

def readmvei(path):
  # read header
  (width, height, channels, dtype) = readmveiheaders(path)

  # read image
  with Path(path).open('rb') as f:
    f.seek(11+4*4)
    return np.fromfile(f, dtype=dtype, count=width*height*channels).reshape((height, width, channels))


def readbundle(path):
  cameras=list()
  features=list()
  with Path(path).open('r') as f:
    header = f.readline().strip()
    if header != 'drews 1.0':
      raise Exception("unsupported bundle file (%s)" % header)
    (nbcameras, nbfeatures) = f.readline().strip().split(' ')
    for i in range(int(nbcameras)):
      (focal, k1, k2) = f.readline().strip().split(' ')
      (r11, r12, r13) = f.readline().strip().split(' ')
      (r21, r22, r23) = f.readline().strip().split(' ')
      (r31, r32, r33) = f.readline().strip().split(' ')
      (tx,   ty,  tz) = f.readline().strip().split(' ')
      cameras.append({
        'focal_length': float(focal),
        'distortion': [float(k1), float(k2)],
        'rotation': np.array(
          [
            [float(r11), float(r12), float(r13)],
            [float(r21), float(r22), float(r23)],
            [float(r31), float(r32), float(r33)]
          ],
          dtype=np.float64
        ),
        'translation': np.array(
          [float(tx), float(ty), float(tz)],
          dtype=np.float64
        )
      })
    # TODO: read features?
  return cameras


class MVEView(object):
  def __init__(self, scene, path):
    self.scene = scene
    self.path = path
    meta = ConfigParser()
    meta.read(path / 'meta.ini')
    if 'view' in meta:
      self.id = int(meta['view']['id'])
      self.name = meta['view']['name']
    else:
      self.id = -1
      self.name = None
    self.rotation = np.eye(4, dtype=np.float64)
    self.translation = np.zeros(3, dtype=np.float64)
    if 'camera' in meta:
      self.camera = self.scene.cameras[self.id]
      self.focal_length = float(meta['camera']['focal_length'])
      self.distortion = self.camera['distortion']
      self.pixel_aspect = float(meta['camera']['pixel_aspect'])
      self.principal_point = np.array(
        [ float(x) for x in meta['camera']['principal_point'].strip().split(' ') ],
        dtype=np.float64
      )
      self.rotation[0:3,0:3] = np.array(
        [ float(x) for x in meta['camera']['rotation'].strip().split(' ') ],
        dtype=np.float64
      ).reshape((3,3))
      self.translation = np.array(
        [ float(x) for x in meta['camera']['translation'].strip().split(' ') ],
        dtype=np.float64
      )
      if self.focal_length > 0:
        df = abs(self.camera['focal_length'] - self.focal_length)
        if not df < 1e-3:
          print("bundle != view %d meta (focal_length:%e)" % (self.id, df))
        dr = np.abs(self.camera['rotation'] - self.rotation[0:3,0:3]).flat
        if not np.all(dr < 1e-3):
          print("bundle != view %d meta (rotation:[%e,%e,%e,%e,%e,%e,%e,%e,%e])" % (self.id, dr[0], dr[1], dr[2], dr[3], dr[4], dr[5], dr[6], dr[7], dr[8]))
        dt = np.abs(self.camera['translation'] - self.translation)
        if not np.all(dt < 1e-3):
          print("bundle != view %d meta (translation:[%e,%e,%e])" % (self.id, dt[0], dt[1], dt[2]))
    else:
      self.focal_length = 0.0
      self.distortion = [0.0, 0.0]
      self.pixel_aspect = 1.0
      self.principal_point = np.zeros(2)
      self.rotation = np.eye(4, dtype=np.float64)
      self.translation = np.zeros((3), dtype=np.float64)
    if self.original():
      image = Image.open(self.original())
      self.width = image.size[0]
      self.height = image.size[1]
    else:
      self.width = 0
      self.height = 0
    if self.depthcolor():
      image = Image.open(self.depthcolor())
      self.depthWidth = image.size[0]
      self.depthHeight = image.size[1]
    else:
      self.depthWidth = 0
      self.depthHeight = 0

  def toJSON(self):
    return {
      'id': self.id,
      'name': self.name,
      'focal_length': self.focal_length,
      'distortion': self.distortion,
      'pixel_aspect': self.pixel_aspect,
      'principal_point': self.principal_point.tolist(),
      'rotation': self.rotation.tolist(),
      'translation': self.translation.tolist(),
      'size': [self.width, self.height],
      'original': self.original(),
      'thumbnail': self.thumbnail(),
      'undistorted': self.undistorted(),
      'depth': self.depth(),
      'depthcolor': self.depthcolor(),
      'depthviews': self.depthviews(),
      'depthsize': [self.depthWidth, self.depthHeight],
    }

  def __repr__(self):
    return json.dumps(self.toJSON())

  def __str__(self):
    return json.dumps(self.toJSON(), indent='  ')

  def valid(self):
    return self.id >= 0

  def ready(self):
    return self.valid() and self.focal_length > 0

  def robust(self, min_focal=0.5, max_focal=1.0, max_dist=5):
    return self.ready() and self.focal_length >= min_focal and self.focal_length <= max_focal and abs(self.distortion[0]) < max_dist and abs(self.distortion[1]) < max_dist

  def intrinsic(self, width, height, near, far):
    a = width / max(height, 1) * self.pixel_aspect
    if a < 1.0:
      ax = self.focal_length / a
      ay = self.focal_length
    else:
      ax = self.focal_length
      ay = self.focal_length * a

    p = np.zeros((4,4), dtype=np.float64)
    p[0,0] = 2 * ax
    # p[0,1] = 0 #sheer
    p[0,2] = 2 * (self.principal_point[0] - 0.5)
    p[1,1] = 2 * ay
    p[1,2] = 2 * (self.principal_point[1] - 0.5)
    p[2,2] = (near + far) / (near - far)
    p[2,3] = 2 * near * far / (near - far)
    p[3,2] = -1
    return p

  def camera2world(self):
    m = self.rotation.T.copy()
    m[0:3,3] = self.position()
    return m

  def world2camera(self):
    m = self.rotation.copy()
    m[0:3,3] = self.translation
    m[1:3,:] = -m[1:3,:]
    return m


  def position(self):
    return -(self.rotation[0:3,0:3].T @ self.translation)

  def original(self):
    path = self.path / 'original.jpg'
    if path.exists():
      return str(path)
    return None

  def thumbnail(self):
    path = self.path / 'thumbnail.png'
    if path.exists():
      return str(path)
    return None

  def undistorted(self):
    path = self.path / 'undistorted.png'
    if path.exists():
      return str(path)
    return None

  def depth(self):
    for path in sorted(self.path.glob('depth-L*.mvei')):
      return str(path)
    return None

  def depthcolor(self):
    for path in sorted(self.path.glob('depth-L*.mvei')):
      path = path.with_name(path.stem.replace('depth', 'undist') + '.png')
      if path.exists():
        return str(path)
    return self.undistorted()

  def depthviews(self):
    for path in sorted(self.path.glob('depth-L*.mvei')):
      path = path.with_name(path.stem.replace('depth', 'views') + '.mvei')
      if path.exists():
        return str(path)
    return None

  def ply(self):
    path = self.path / 'pointcloud.ply'
    if path.exists():
      return str(path)
    path = self.path / 'pointcloud.ply.gz'
    if path.exists():
      return str(path)
    path = self.path / 'pointcloud.ply.xz'
    if path.exists():
      return str(path)
    return None

  def readoriginal(self):
    return cv2.imread(self.original())

  def readthumbnail(self):
    return cv2.imread(self.thumbnail())

  def readundistorted(self):
    return cv2.imread(self.undistorted())

  def readdepth(self):
    return readmvei(self.depth())

  def readdepthcolor(self):
    return cv2.imread(self.depthcolor())

  def readdepthviews(self):
    return readmvei(self.depthviews())


class MVEViews(object):
  def __init__(self, scene):
    self.scene = scene
    self.path = self.scene.path / 'views'
    self.items = sorted(
      [ view for view in [ MVEView(self.scene, child) for child in self.path.iterdir() if child.is_dir() ] if view.valid() ],
      key=lambda v: v.id
    )

  def toJSON(self):
    return [ item.toJSON() for item in self.items ]

  def __repr__(self):
    return json.dumps(self.toJSON())

  def __str__(self):
    return json.dumps(self.toJSON(), indent='  ')

  def validitems(self):
    return [ view for view in self.items if view.ready() ]

  def robustitems(self, min_focal=0.5, max_focal=1.0, max_dist=5):
    return [ view for view in self.items if view.robust(min_focal, max_focal, max_dist) ]


class MVEScene(object):
  def __init__(self, path):
    self.path = Path(path)
    self.cameras = readbundle(self.path / 'synth_0.out')
    self.views = MVEViews(self)

  def toJSON(self):
    return {
      'path': str(self.path),
      'cameras': self.cameras,
      'views': self.views.toJSON()
    }

  def __repr__(self):
    return json.dumps(self.toJSON())

  def __str__(self):
    return json.dumps(self.toJSON(), indent='  ')
