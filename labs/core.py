from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING :
  from typing import Callable
  
from . import main

def _attr_label(attr_name:str):
  if attr_name.startswith('_internal.') :
    return attr_name[10:]
  if attr_name[0] in ( '.', '_'):
    return attr_name[1:]
  return attr_name

def _update_attrs(current:dict, new:dict):
  keyset = { _attr_label : attr for attr in current.keys() }
  toremobv


def _repr_attr_getattr(self, attr):
  return getattr(self, attr)

def _repr_attr_self(self, attr):
  return self

def _repr_attr_internal(self, attr):
  return getattr(self._internal, attr)

def _parse_repr_attr(attr:str):
  if attr == 'self' :
    return '', _repr_attr_self, False, attr
  
  print_label = attr[-1] == '='
  if print_label :
    attr = attr[:-1]
  func = _repr_attr_getattr
    
  if attr[0] == '.' :
    attr = attr[1:]
    func = _repr_attr_self
  elif attr.startswith('_internal.') :
    attr = attr[10:]
    func = _repr_attr_internal
    
  label = attr
  if label[0] == '_':
    label = label[1:]

  return label, func, print_label, attr

def _make_attr_cache(attr_dict):
  return {
    label: content
    for label, *content in (
      (*_parse_repr_attr(attr), attr, cast)
      for attr, cast in attr_dict.items()
    )
  }
  

class LabsObject(object):
  """
  Base class of all labs object, to provide helpful feature for debugging introspection etc.
  """
  
  _repr_attrs = {}
  _all_repr_attrs = {}
  _cache_repr_attrs:dict[tuple[Callable, bool, str, str, Callable]] = {} # label -> (repr_handler, should_print_label, lookup_attr, original_attr_string, cast_function)


  def __init_subclass__(cls, **kwargs):
    super().__init_subclass__(**kwargs)
    cache = {}
    if '_all_repr_attrs' not in cls.__dict__ :
      for parent in reversed(cls.__bases__) :
        if issubclass(parent, LabsObject) :
          cache.update(parent._cache_repr_attrs)
    else : 
      cache.update(_make_attr_cache(cls._all_repr_attrs))
    if '_repr_attrs' in cls.__dict__ :
      cache.update(_make_attr_cache(cls._repr_attrs))
    cls._all_repr_attrs = { original: cast for func, print_label, attr, original, cast in cache.values()}
    cls._cache_repr_attrs = cache

  def _repr_attr(self, label, content):
    func, print_label, attr, _, cast = content
    val = func(self, attr)
    if cast :
      val = cast(val)
    if print_label :
      return f'{label}={val}'
    return val

  def __repr__(self):
    attrs = ', '.join( self._repr_attr(label, content) for label, content in self._cache_repr_attrs.items() )
    return f'{self.__class__.__name__}({attrs})'
    
class UseInternal(object):
  class _Internal(object):
    def __init__(self, parent, *args, **kwargs):
      self.parent = parent
      self.args = args
      for key, val in kwargs.items() :
        setattr(self, key, val)
      

  def __init__(self, *args, **kwargs):
    self._internal: self._Internal
    object.__setattr__(self, '_internal', self._Internal(self, *args, **kwargs))
 
class FormatDispatcher(object):
  """
  Implements __format__ to dispatch to format_cache_reference, format_expanded and format_ref
  """
    
  def __format__(self, spec):
    return format_functions[spec](self)
  
canonical_format = {}
format_functions = {}

def register_formatter(function, *specs):
    canonical_format.update({ s : specs[0] for s in specs })
    format_functions.update({ s : function for s in specs })

generators = {}

def register_generator(generator, name):
  generators[name] = generator

def generator(name):
  def decorator(f):
    register_generator(f, name)
  return decorator

class UnkownGeneratorError(RuntimeError):
  def __init__(self, generator_lvariable):
    possible_values = ', '.join(repr(name) for name in generators.keys())
    super().__init__(f'Generator {repr(generator_lvariable.value)} unknown (value from {repr(generator_lvariable)}). Probable causes are either a missing extension, a typo, or the generator is not implemented. Possible values are : {possible_values})')
  

class Formatter(LabsObject):
  """
  A formater for a labs object
  """
  _repr_attrs = {'name': repr, 'self': lambda self: 'Compatible types: ' + ', '.join( t.__name__ for types, _ in self.subs for t in types )}

  def __init__(self, *specs:str):
    register_formatter(self, *specs)
    self.name = specs[0] if specs else 'None'
    self.subs = []

  def sub(self, *types:type):
    def decorator(f):
      self.subs.append((types, f))
    return decorator

  def __call__(self, _self):
    try :
      f = next(f for types, f in self.subs if isinstance(_self, types))
    except StopIteration:
      raise TypeError()
    return f(_self)


def formatter(*specs):
  def decorator(f):
    register_formatter(f, *specs)
    return f
  return decorator


escape_functions = {}

def register_escape_function(escape_function, *specs):
  escape_functions.update({ s : escape_function for s in specs })
  
def escape_function(*specs):
  def decorator(f):
    register_escape_function(f, *specs)
    return f
  return decorator

def escape(s:str, spec:str):
  # TODO: test (covered by current tests, but can silently ignore errors
  canonical = canonical_format.get(spec)
  escape_function = escape_functions.get(canonical)
  if not escape_function :
    raise ValueError(f"Invalid format specifier '{spec}' to escape string value")
  return escape_function(s)
    

