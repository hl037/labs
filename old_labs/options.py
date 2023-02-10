from functools import cached_property
from . import runtime as rt
from .cmake import str2bool
from pathlib import Path
from collections import namedtuple

class MetaDeclaredOptionType(type):
  def __str__(self):
    return self.cache_name

class DeclaredOptionType(metaclass=MetaDeclaredOptionType):
  """
  String serialisable declared option type
  """
  cache_name = ''
  @classmethod
  def as_str(cls, val):
    raise NotImplementedError()

  @classmethod
  def as_val(cls, str):
    raise NotImplementedError()

class STRING(DeclaredOptionType):
  cache_name = 'STRING'
  as_str = str
  as_val = str

class INT(DeclaredOptionType):
  cache_name = 'INT'
  as_str = str
  as_val = int
  
class FLOAT(DeclaredOptionType):
  cache_name = 'FLOAT'
  as_str = str
  as_val = float
    
class BOOL(DeclaredOptionType):
  cache_name = 'BOOL'
  as_str = str
  as_val = str2bool

class PATH(DeclaredOptionType):
  cache_name = 'PATH'
  as_str = str
  as_val = Path

class FILEPATH(DeclaredOptionType):
  cache_name = 'FILEPATH'
  as_str = str
  as_val = Path
    
class DeclaredOption(namedtuple('DeclaredOption', ['name', 'type', 'default_value', 'description', 'project'])):
  """
  Represent a user-configurable option
  """
  @property
  def value(self):
    return self.type.as_val(self.project.config[self.name])

  @value.setter
  def value(self, v):
    self.project.config[self.name] = self.type.as_str(v)


class LazyOptions(object):
  """
  Group variables, but add them to the context only if they are requested.
  """
  def __init__(self):
    self._d = {}
  
  def _add(self, name, type, default_value, description):
    self._d[name] = (name, type, default_value, description)

  def __getattr__(self, name):
    ctx = rt.get_ctx()
    return ctx.project.declare_option(*self._d[name])

  def _override(self, *, suffix, prefix=''):
    res = LazyOptions()
    res._d = { prefix + k : (prefix + k, *_) for k, (name, *_) in self._d.items() }
    return res


