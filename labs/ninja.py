from pathlib import Path
from itertools import chain
import operator as op
from addict import Dict as C


def _defOps(a, loc):
  _op = f'__{a}__'
  _rop = f'__r{a}__'
  _iop = f'__i{a}__'
  def o(self, oth):
    if not isinstance(oth, self.__class__) :
      oth = self.__class__(oth)
    return self.__class__(getattr(op, _op)(self.paths, oth.paths))
  def ro(self, oth):
    if not isinstance(oth, self.__class__) :
      oth = self.__class__(oth)
    return self.__class__(getattr(op, _op)(oth.paths, self.paths))
  def io(self, oth):
    if not isinstance(oth, self.__class__) :
      oth = self.__class__(oth)
    getattr(op, _iop)(self.paths, oth.paths)
    return self
  o.__name__ = _op
  ro.__name__ = _rop
  io.__name__ = _iop
  loc[_op] = o
  loc[_rop] = ro
  loc[_iop] = io



class Target(object):
  """
  Set of explicit/implicit input/output files
  """
  def __init__(self, *args):
    if len(args) == 1 and isinstance(args[0], Target) :
      self.paths = set(args[0].paths)
    else:
      self.paths = set(chain.from_iterable( (Path(a),) if isinstance(a, (Path, str)) else map(Path, a) for a in args))

  def __iter__(self):
    return iter(self.paths)

  for a in (
    'or',
    'xor',
    'and',
    'sub'
  ):
    _defOps(a, locals())
  del a

  def __len__(self):
    return len(self.paths)

  def toNinja(self):
    return ' '.join(escape(str(p)) for p in sorted(self.paths))
      
del _defOps

class Expr(object):
  """
  Represents a string with reference to a variable
  """
  def __init__(self, v):
    if isinstance(v, self.__class__) :
      self.value = v.value
    elif isinstance(v, (str, Variable)) :
      self.value = [v]
    else:
      raise ValueError('Expr() accepts only other exprs, str, or Variable')

  def __add__(self, other):
    e = self.__class__(other)
    e.value = self.value + e.value
    return e
    
  def __radd__(self, other):
    e = self.__class__(other)
    e.value = e.value + self.value
    return e
    
  def __iadd__(self, other):
    e = self.__class__(other)
    self.value += e.value
    return self

  def __str__(self):
    return ''.join(escape(s) if isinstance(s, str) else str(s) for s in self.value)
    

class Variable(object):
  """
  A toplevel variable. 
  """
  def __init__(self, name, val=''):
    self.name = str(name)
    self.val = str(val)
    
  def __add__(self, other):
    return Expr(self) + other
    
  def __radd__(self, other):
    return Expr(other) + self

  def __str__(self):
    return f'${{{self.name}}}'

  def toNinja(self):
    return f'{self.name} = {self.val}'

class VariableBuiltin(Variable):
  def toNinja(self):
    raise NotImplementedError()

class VariableRule(VariableBuiltin):
  pass


class BuildTarget(object):
  """
  """
  def __init__(self):
    self.i = Target()
    self.o = Target()

  def __get__(self, obj, owner=None):
    return self

  def __set__(self, obj, val):
    raise AttributeError()

  def __delete__(self, obj, val):
    raise AttributeError()

  def __lshift__(self, oth):
    self.i |= oth

  __rrshift__ = __lshift__
  
  def __rshift__(self, oth):
    self.o |= oth

  __rlshift__ = __rshift__

class BuildInputTarget(object):
  """
  """
  def __init__(self):
    self.i = Target()

  def __get__(self, obj, owner=None):
    return self

  def __set__(self, obj, val):
    raise AttributeError()

  def __delete__(self, obj, val):
    raise AttributeError()

  def __lshift__(self, oth):
    self.i |= oth

  __rrshift__ = __lshift__

class QualifiedTarget(object):
  """
  Helper class to use the bitwise shift operator as a dependency injection
  """
  def __init__(self, explicit=Target(), implicit=Target(), order_only=Target()):
    self.explicit = explicit
    self.implicit = implicit
    self.order_only = order_only
    
  def __lshift__(self, oth):
    if isinstance(oth, Build) :
      if len(self.order_only) != 0 :
        raise ValueError('''A build can't produce "order-only" output targets''')
      oth.explicit.o   |= self.explicit
      oth.implicit.o   |= self.implicit
      return oth
    if not isinstance(oth, QualifiedTarget) :
      oth = explicit(oth)
    return self.__class__(self.explicit | oth.explicit, self.implicit | oth.implicit, self.order_only | oth.order_only)

  __rrshift__ = __lshift__
  
  def __rshift__(self, oth):
    if isinstance(oth, Build) :
      oth.explicit.i   |= self.explicit
      oth.implicit.i   |= self.implicit
      oth.order_only.i |= self.order_only
      return oth
    if not isinstance(oth, QualifiedTarget) :
      oth = explicit(oth)
    return self.__class__(self.explicit | oth.explicit, self.implicit | oth.implicit, self.order_only | oth.order_only)

  __rlshift__ = __rshift__

  

class Build(object):
  """
  Build section of ninja
  """
  def __init__(self, rule:'Rule', *args, **kwargs):
    self.rule = rule
    self.v = C(kwargs)
    for k, v in args :
      self.v[k] = v
    self.explicit = BuildTarget()
    self.implicit = BuildTarget()
    self.order_only = BuildInputTarget()

  def __lshift__(self, oth):
    if isinstance(oth, QualifiedTarget) :
      return NotImplemented
    return explicit(oth) >> self

  __rrshift__ = __lshift__
  
  def __rshift__(self, oth):
    if isinstance(oth, QualifiedTarget) :
      return NotImplemented
    return explicit(oth) << self

  __rlshift__ = __rshift__
    

  def toNinja(self):
    variables = '\n  '.join(f'{k} = {str(Expr(v))}' for (k, v) in self.v.items())
    if len(self.explicit.o) == 0 and len(self.implicit.o) == 0 :
      raise RuntimeError('This build rule has no output')
      

    return (
      "build "
      f"{self.explicit.o.toNinja()}"
      f"{( ' | '  + self.implicit.o.toNinja())   if self.implicit.o   else ''}"
      " : "
      f"{self.rule.name} "
      f"{self.explicit.i.toNinja()}"
      f"{( ' | '  + self.implicit.i.toNinja())   if self.implicit.i   else ''}"
      f"{( ' || ' + self.order_only.i.toNinja()) if self.order_only.i else ''}"
      f"\n  {variables}"
    )   

class Rule(object):
  """
  Rule section of ninja
  """
  Build = Build

  def __init__(self, name, **kwargs):
    self.name = name
    self.v = C(kwargs)

  @classmethod
  def __init_subclass__(cls, /, Build_cls=Build, **kwargs):
    super().__init_subclass__(**kwargs)
    cls.Build = Build_cls


  def toNinja(self):
    if 'command' not in self.v :
      raise RuntimeError(f"Missing the required 'command' variable in the rule {self.name} : {repr(self)}")
    variables = '\n  '.join(f'{k} = {str(Expr(v))}' for (k, v) in self.v.items())
    return f'rule {self.name}\n  {variables}'

  def build(self, **kwargs):
    return self.Build(self, **kwargs)


def explicit(*args):
  return QualifiedTarget(explicit=Target(*args))
def implicit(*args):
  return QualifiedTarget(implicit=Target(*args))
def order_only(*args):
  return QualifiedTarget(order_only=Target(*args))

def escape(s):
  for k, v in [
    ('$' , '$$'),
    (' ' , '$ '),
    (':' , '$:'),
    ('\n', '$\n'),
  ]:
    s = s.replace(k, v)
  return s

v_command = VariableBuiltin('command')
v_depfile = VariableBuiltin('depfile')
v_deps = VariableBuiltin('deps')
v_msvc_deps_prefix = VariableBuiltin('msvc_deps_prefix')
v_description = VariableBuiltin('description')
v_dyndep = VariableBuiltin('dyndep')
v_generator = VariableBuiltin('generator')
v_in = VariableBuiltin('in')
v_in_newline = VariableBuiltin('in_newline')
v_out = VariableBuiltin('out')
v_restat = VariableBuiltin('restat')
v_rspfile = VariableBuiltin('rspfile')
v_rspfile_content = VariableBuiltin('rspfile_content')


