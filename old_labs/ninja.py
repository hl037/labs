from pathlib import Path
from itertools import chain
import operator as op
from .utils import Dict
import shlex
from collections import namedtuple
from typing import Callable
from functools import partial
from typing import Union


def _defOps(a, loc):
  _op = f'__{a}__'
  _rop = f'__r{a}__'
  _iop = f'__i{a}__'
  def o(self, oth):
    if not isinstance(self, oth.__class__) :
      if isinstance(oth, Target) :
        return NotImplemented
      oth = self.__class__(oth)
    return self.__class__(getattr(op, _op)(self.paths, oth.paths))
  def ro(self, oth):
    if not isinstance(self, oth.__class__) :
      if isinstance(oth, Target) :
        return NotImplemented
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
      self.paths = set(chain.from_iterable(
        (
          (a,)       if isinstance(a, Expr) else
          (Expr(a),) if isinstance(a, (Path, str)) else
          map(Expr, a)
        )
        for a in args
      ))

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

  def str_sorted(self):
    return sorted(map(str, self.paths))

  def toNinja(self):
    return ' '.join(str(e) for e in self.str_sorted())
      
del _defOps

class IncompatibleExprContext(RuntimeError):
  pass

class Expr(object):
  """
  Represents a string with reference to a variable
  """
  def __init__(self, v):
    if isinstance(v, self.__class__) :
      self.value = v.value
      self._str = v._str
      self.context = None
    elif isinstance(v, Path) :
      self.value = [str(v)]
      self._recompute_str()
      self.context = None
    elif isinstance(v, (str, Variable)) :
      self.value = [v]
      if isinstance(v, VariableRule) :
        self.context = v.rule
      elif isinstance(v, VariableBuild) :
        self.context = v.build
      else :
        self.context = None
      self._recompute_str()
    else:
      raise ValueError('Expr() accepts only other exprs, str, or Variable')
      self.value = None
      self._str = None
      self.context = None

  @classmethod
  def is_compatible(cls, obj):
    return isinstance(obj, (Expr, Variable, Path, str))

  @classmethod
  def getContext(cls, o1, o2):
    # Sort in inheritance order
    if ((isinstance(o2, VariableBuild) and not isinstance(o1, VariableBuild)) or 
        (isinstance(o2, VariableRule) and o1 is None)):
      o1, o2 = o2, o1
    if isinstance(o1, VariableRule) :
      if o2 is None :
        if isinstance(o1, VariableBuild) :
          return o1.build
        return o1.rule
      if o1.rule is not o2.rule :
        raise IncompatibleExprContext(f'Between {o1.rule} and {o2.rule}')
      if isinstance(o1, VariableBuild) :
        if not isinstance(o2, VariableBuild) :
          return o1.build
        if o1.build is not o2.build :
          raise IncompatibleExprContext(f'Between {o1.build} and {o2.build})')
        return o1.build
      return o1.rule
        
  def __add__(self, other):
    e = self.__class__(other)
    e.value = self.value + e.value
    e.context = self.getContext(self, other)
    e._recompute_str()
    return e
    
  def __radd__(self, other):
    e = self.__class__(other)
    e.value = e.value + self.value
    e.context = self.getContext(self, other)
    e._recompute_str()
    return e
    
  def __iadd__(self, other):
    e = self.__class__(other)
    self.value += e.value
    e.context = self.getContext(self, other)
    self._recompute_str()
    return self

  def _recompute_str(self):
    self._str = ''.join(escape(s) if isinstance(s, str) else str(s) for s in self.value)
    
  def __str__(self):
    return self._str

  def __eq__(self, oth):
    if not isinstance(oth, self.__class__) :
      return NotImplemented
    return self._str == oth._str and self.context is oth.context

  def __hash__(self):
    return hash((self._str, self.context))

  def __lt__(self, oth):
    if not isinstance(oth, self.__class__) :
      return NotImplemented
    return self._str < oth._str
    

class Variable(object):
  """
  A toplevel variable. 
  """
  def __init__(self, name, value=''):
    self.name = str(name)
    self.value = Expr(str(value))
    
  def __add__(self, other):
    return Expr(self) + other
    
  def __radd__(self, other):
    return Expr(other) + self

  def __str__(self):
    return f'${{{self.name}}}'

  def toNinja(self):
    return f'{self.name} = {self.value}'

class VariableBuiltin(Variable):
  def toNinja(self):
    raise NotImplementedError()

class VariableRule(Variable):
  """
  A top level variable scoped to a rule
  """
  def __init__(self, rule:'Rule', name:str, value:str=''):
    super().__init__(name=f'_Rule_{rule.name}_var_{name}_', value=value)
    self._name = name
    self.rule = rule

class VariableBuild(VariableRule):
  """
  A build variable
  """
  def __init__(self, build:'Build', name:str, value:str=''):
    super().__init__(build.rule,name, value)
    self.build = build
  

class BuildTarget(object):
  """
  """
  def __init__(self):
    self.i = Target()
    self.o = Target()

  def __get__(self, obj, owner=None):
    return self

  def __set__(self, obj, value):
    raise AttributeError()

  def __delete__(self, obj, value):
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

  def __set__(self, obj, value):
    raise AttributeError()

  def __delete__(self, obj, value):
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


class VariableProxy(VariableBuiltin):
  def __init__(self, name, d):
    self.name = name
    self.d = d

  @property
  def value(self):
    return self.d[self.name]

  @value.setter
  def value(self, v):
    self.d[self.name] = v


class VariableDict(dict):
  """
  Helper class that keeps attributes outside the dict
  """

  def __self__(self, VariableClass = Variable):
    self._VariableClass_ = Variable
  
  def __setattr__(self, k, val):
    if k in self.__dict__ :
      self.__dict__[k] = val
    else :
      self[k].value = val

  def __getattr__(self, k):
    return self[k]

  def __missing__(self, k):
    v = self._VariableClass_(k, '')
    self[k] = v
    return v

  def new_variable(self, k, v=None):
    res = self[k]
    if v is not None :
      res.value = v
    return res

class Build(dict):
  """
  Build section of ninja
  """
  def __init__(self, rule:'Rule', *args, **kwargs):
    object.__setattr__(self, 'rule', rule)
    for k, v in args :
      self[k] = v
    self.update(kwargs)
    object.__setattr__(self, 'explicit', BuildTarget())
    object.__setattr__(self, 'implicit', BuildTarget())
    object.__setattr__(self, 'order_only', BuildInputTarget())

  def __missing__(self, k):
    return self.rule[k].value

  def __getattr__(self, k):
    return self[k]

  def __setattr__(self, k, val):
    if k in self.__dict__ :
      self.__dict__[k] = val
    else :
      self[k] = val

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
    variables = ''.join(f'\n  {k} = {str(Expr(v))}' for (k, v) in self.items())
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
      f"{variables}"
    )

  def __repr__(self):
    return self.toNinja()

class Rule():
  """
  Rule section of ninja
  """
  Build = Build
  builtin = set()

  def __init__(self, name, rule_variables={}, **kwargs):
    kwargs.update(rule_variables)
    object.__setattr__(self, 'name', name)
    object.__setattr__(self, '_v', VariableDict(partial(VariableRule, self)))
    object.__setattr__(self, '_b', VariableDict(VariableBuiltin))
    for k, v in kwargs.items() :
      if isinstance(v, Expr) :
        v.value = [ (x.create_from(self) if isinstance(x, FutureVariable) else x) for x in v.value ]
      setattr(self, k, v)
      

  @classmethod
  def __init_subclass__(cls, /, Build_cls=Build, **kwargs):
    super().__init_subclass__(**kwargs)
    cls.Build = Build_cls

  def toNinja(self):
    if 'command' not in self._b :
      raise RuntimeError(f"Missing the required 'command' variable in the rule {self.name} : {repr(self)}")
    variables_rule = '\n'.join(f'{k} = {str(Expr(v.value))}' for (k, v) in self._v.items())
    variables_builtin = '\n  '.join(f'{k} = {str(Expr(v.value))}' for (k, v) in self._b.items())
    return (
      f'{variables_rule}\n'
      f'rule {self.name}\n'
      f'  {variables_builtin}'
    )

  def build(self, **kwargs):
    return self.Build(self, **kwargs)

  def __repr__(self):
    variables_rule = '\n'.join(f'{k} = {str(Expr(v.value))}' for (k, v) in self._v.items())
    variables_builtin = '\n  '.join(f'{k} = {str(Expr(v.value))}' for (k, v) in self._b.items())
    return (
      f'{variables_rule}\n'
      f'rule {self.name}\n'
      f'  {variables_builtin}'
    )

  def __getattr__(self, k) -> VariableProxy:
    return self[k]

  def __setattr__(self, k, val):
    if k in self.__dict__ :
      self.__dict__[k] = val
    else :
      self[k].value = val

  def __getitem__(self, k) -> VariableProxy:
    if k in self.builtin :
      return self._b[k]
    return self._v[k]

  def __setitem__(self, k, v):
    if k in self.builtin:
      self._b[k] = val
    else :
      self._v[k] = val

  def items(self):
    return chain(self._b.items(), self._v.items())
  
  def keys(self):
    return chain(self._b.keys(), self._v.keys())

  def values(self):
    return chain(self._b.values(), self._v.values())

  def new_variable(self, k, v) -> VariableProxy:
    res = self[k]
    res.value = v
    return res


def explicit(*args) -> QualifiedTarget:
  return QualifiedTarget(explicit=Target(*args))
def implicit(*args) -> QualifiedTarget:
  return QualifiedTarget(implicit=Target(*args))
def order_only(*args) -> QualifiedTarget:
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

def quote_arg_list(*args, variable_factory:Callable[[str, Expr], Variable]=None) -> Expr:
  if len(args) == 1 and not isinstance(args[0], (str, Variable)) :
    args = args[0]
  if variable_factory is not None :
    args = [ (variable_factory(a.name, a.value) if isinstance(a, FutureVariable) else a) for a in args ]
  e = Expr(args[0])
  for a in args[1:] :
    e += ' '
    e += a if isinstance(a, (Variable, Expr)) else shlex.quote(str(a))
  return e

class FutureVariable(VariableBuiltin):
  """
  Class to be used to call function that need an expression constructed with variable created from on object not existing yet.
  """
  def __init__(self, *args, **kwargs):
    if len(args) == 1 :
      if isinstance(args[0], str) :
        self.name = args[0]
        self._value = None
      else:
        self.name, self._value = args[0]
    elif len(args) == 2 :
      self.name, self._value = args
    elif len(kwargs) == 1 :
      self.name, self._value = kwargs.popitem()
    else:
      raise TypeError(f'{self.__class__.__name__}.__init__ expects as argument either a tuple (name, value), either 2 arguments name, value, either 1 keyword argument name=value')
  
  @property
  def value(self):
    return self._value if self._value is not None else ''

  @value.setter
  def value(self, v):
    self._value = v

  def create_from(self, instance):
    return instance.new_variable(self.name, self._value)


V = FutureVariable

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

builtin_variables = { v.name : v for v in (
  v_command,
  v_depfile,
  v_deps,
  v_msvc_deps_prefix,
  v_description,
  v_dyndep,
  v_generator,
  v_in,
  v_in_newline,
  v_out,
  v_restat,
  v_rspfile,
  v_rspfile_content
)}

Rule.builtin.update(builtin_variables.keys())

__all__ = [
  'Target',
  'Expr',
  'Variable',
  'Build',
  'Rule',
  'explicit',
  'implicit',
  'order_only',
  'escape',
  'quote_arg_list',
  'FutureVariable',
  'V',
  *[ ('v_' + n) for n in builtin_variables.keys() ]
]
  


