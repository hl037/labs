from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING :
  pass

from pathlib import Path

from .core import LabsObject, UseInternal, FormatDispatcher
from .variables import Expandable, Expr


class PathObject(LabsObject, FormatDispatcher):
  """
  Base class for paths with metadata. There is always one instance per path, so that the metadata are always shared.
  """
  def __init__(self, path:Path):
    self.path = path

class PathList(object):
  """
  A set of paths
  """
  def __init__(self, *paths):
    if len(paths) == 1 and not isinstance(paths[0], PathObject) :
      self.paths = list(paths[0])
    else :
      self.paths = paths
    
