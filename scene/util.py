from PySide2.QtCore import QMutex, QMutexLocker


class ObjectProxy(object):
  __slots__ = ["_obj", "__weakref__"]


  def __init__(self, obj=None):
    self.apply(obj)


  def apply(self, obj):
    object.__setattr__(self, "_obj", obj)


  def __nonzero__(self):
    obj = object.__getattribute__(self, "_obj")
    return bool(obj)

  def __str__(self):
    obj = object.__getattribute__(self, "_obj")
    return str(obj)

  def __repr__(self):
    obj = object.__getattribute__(self, "_obj")
    return repr(obj)

  def __getattribute__(self, name):
    if name == 'apply':
      return object.__getattribute__(self, name)
    obj = object.__getattribute__(self, "_obj")
    if not obj:
      raise Exception("no object on proxy")
    return getattr(obj, name)

  def __setattr__(self, name, value):
    obj = object.__getattribute__(self, "_obj")
    if not obj:
      raise Exception("no object on proxy")
    setattr(obj, name, value)


class SynchronizedObjectProxy(object):
  __slots__ = ["_mutex", "_obj", "_methods", "__weakref__"]


  def __init__(self, obj=None):
    object.__setattr__(self, "_mutex", QMutex(QMutex.Recursive))
    self.apply(obj)


  def apply(self, obj):
    mutex = object.__getattribute__(self, "_mutex")
    methods = dict()
    if obj:
      for key in dir(obj):
        if not callable(getattr(obj, key)):
          continue
        if key.startswith('__') or key.endswith('__'):
          continue
        methods[key] = SynchronizedMethodProxy(mutex, obj, getattr(obj, key))
    object.__setattr__(self, "_obj", obj)
    object.__setattr__(self, "_methods", methods)

  def lock(self):
    mutex = object.__getattribute__(self, "_mutex")
    mutex.lock()

  def unlock(self):
    mutex = object.__getattribute__(self, "_mutex")
    mutex.unlock()

  def __nonzero__(self):
    with QMutexLocker(object.__getattribute__(self, "_mutex")) as locker:
      obj = object.__getattribute__(self, "_obj")
      return bool(obj)

  def __str__(self):
    with QMutexLocker(object.__getattribute__(self, "_mutex")) as locker:
      obj = object.__getattribute__(self, "_obj")
      return str(obj)

  def __repr__(self):
    with QMutexLocker(object.__getattribute__(self, "_mutex")) as locker:
      obj = object.__getattribute__(self, "_obj")
      return repr(obj)

  def __getattribute__(self, name):
    if name == 'apply' or name == 'lock' or name == 'unlock':
      return object.__getattribute__(self, name)
    obj = object.__getattribute__(self, "_obj")
    if not obj:
      raise Exception("no object on proxy")
    methods = object.__getattribute__(self, "_methods")
    if name in methods:
      return methods[name]
    with QMutexLocker(object.__getattribute__(self, "_mutex")) as locker:
      return getattr(obj, name)

  def __setattr__(self, name, value):
    obj = object.__getattribute__(self, "_obj")
    if not obj:
      raise Exception("no object on proxy")
    methods = object.__getattribute__(self, "_methods")
    if name in methods:
      raise Exception("cannot set method on proxy")
    with QMutexLocker(object.__getattribute__(self, "_mutex")) as locker:
      setattr(obj, name, value)

  def __enter__(self):
    mutex = object.__getattribute__(self, "_mutex")
    mutex.lock()

  def __exit__(self, type, value, tb):
    mutex = object.__getattribute__(self, "_mutex")
    mutex.unlock()


class SynchronizedMethodProxy(object):
  def __init__(self, mutex, obj, method):
    self.mutex = mutex
    self.obj = obj
    self.method = method

  def __call__(self, *args, **kwds):
    with QMutexLocker(self.mutex) as locker:
      return self.method(*args, **kwds)
