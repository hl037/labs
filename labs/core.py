

class LabsObject(object):
  """
  Base class of all labs object, to provide helpful feature for debugging introspection etc.
  """
  
  _repr_attrs = {}
  _all_repr_attrs = {}

  def __init_subclass__(cls, **kwargs):
    super().__init_subclass__(**kwargs)
    if '_all_repr_attrs' not in cls.__dict__ :
      if '_repr_attrs' in cls.__dict__ :
        cls._all_repr_attrs = {**cls._repr_attrs}
      else :
        cls._all_repr_attrs = {}
      for parent in cls.__bases__ :
        if issubclass(parent, LabsObject) :
          cls._all_repr_attrs.update({ attr: cast for attr, cast in parent._all_repr_attrs.items() if attr not in cls._all_repr_attrs })

  def _repr_attr(self, attr:str, cast):
    if attr == 'self' :
      return cast(self)
    
    print_label = attr[-1] == '='
    if print_label :
      attr = attr[:-1]
    obj = None
      
    if attr[0] == '.' :
      attr = attr[1:]
      obj = self
    elif attr.startswith('_internal.') :
      attr = attr[10:]
      obj = self._internal[attr]
      
    label = attr
    if label[0] == '_':
      label = label[1:]

    if obj is None :
      obj = getattr(self, attr)

    if cast :
      value = cast(obj)
    else :
      value = obj
    
    if print_label :
      return f'{label}={value}'
    else :
      return value

  def __repr__(self):
    attrs = ', '.join( self._repr_attr(attr, cast) for attr, cast in self._all_repr_attrs.items() )
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
    global canonical_format
    global format_functions
    canonical_format |= { s : specs[0] for s in specs }
    format_functions |= { s : function for s in specs }
  

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


@staticmethod
def formatter(*specs):
  def decorator(f):
    register_formatter(f, *specs)
    return f
  return decorator
