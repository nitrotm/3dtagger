# selection.py: project selection event
#
# author: Antony Ducommun dit Boudry (nitro.tm@gmail.com)
# license: GPL
#


class ProjectSelection(object):
  def __init__(self, pt, radius, add, time):
    self.pt = pt
    self.radius = radius
    self.add = add
    self.time = time


  def __hash__(self):
    return hash((self.pt, self.radius, self.add))

  def __eq__(self, o):
    return (
      self.pt == o.pt and
      self.radius == o.radius and
      self.add == o.add
    )
