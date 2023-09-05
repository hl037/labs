

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

  def _repr_attr(self, attr, cast):
    if attr == 'self' :
      return cast(self)
    if attr[0] == '_' :
      label = attr[1:]
    else :
      label = attr
    return f'{label}={cast(getattr(self, attr))}'

  def __repr__(self):
    attrs = ', '.join( self._repr_attr(attr, cast) for attr, cast in self._all_repr_attrs.items() )
    return f'{self.__class__.__name__}({attrs})'
    
    
