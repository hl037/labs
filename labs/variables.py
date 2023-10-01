from __future__ import annotations

from enum import Enum, IntEnum
from collections import deque
import labs
from pathlib import Path
import re
import weakref

from .translation import tr
from .core import LabsObject, FormatDispatcher, canonical_format
from labs import cmake

class LVariableAlreadyEvaluatedError(RuntimeError):
  pass

class LVariableTypeInferenceError(RuntimeError):
  #TODO UT
  pass

class VariableReferenceCycleError(RuntimeError):
  def __init__(self, msg, cycle):
    cycle_msg = '->'.join(cycle + [cycle[0]])
    super().__init__(f'{msg} : {cycle_msg}')
  pass

class ExprTypeError(TypeError):
  pass

class VariableTypeMeta(type):
  """
  A meta class to support repr of the vatriable type classes
  """
  def __repr__(self):
    return f'<{self.__name__} LVariable type>'
    

class VariableType(object, metaclass=VariableTypeMeta):
  """
  Variable type.
  This class will hold some utils parse / print variables
  """

  @classmethod
  def loads(cls, s:str) -> str|float|Path|bool: # !abstract
    raise NotImplementedError()

  @classmethod
  def dumps(cls, o:str|float|Path|bool) -> str: # !abstract
    raise NotImplementedError()

  @classmethod
  def typeOf(cls, value:str|int|float|Path|bool):
    t = type(value)
    if t is str :
      return STRING
    elif t is int:
      return INT
    elif t is float :
      return FLOAT
    elif t is bool :
      return BOOL
    elif issubclass(t, Path) :
      return PATH
    else :
      raise TypeError(tr("The value type should be one of str, int, float, Path and bool. Got {type} (value = {value})").format(type=type(value).__name__, value=repr(value)))

  @classmethod
  def cast(cls, value) -> str|float|Path|bool:
    raise NotImplementedError()


class STRING(VariableType):
  @classmethod
  def loads(cls, s:str):
    return s
  
  @classmethod
  def dumps(cls, s:str):
    if not isinstance(s, str) :
      raise TypeError(tr('STRING expects a str. Got {type} (value = {value}).').format(type=type(val).__name__, value=repr(val)))
      # TODO: UT + test ref
    return s

  @classmethod
  def cast(cls, value):
    if isinstance(value, bytes) :
      return value.decode('utf8')
    try :
      return str(value)
    except Exception as e:
      raise TypeError(tr('STRING expects something castable to str. Got {type} (value = {value}). This error occured : {reason}').format(
        type=type(value).__name__,
        value=repr(value),
        reason=str(e))
      ) from e


class INT(VariableType):
  @classmethod
  def loads(cls, s:str):
    try :
      return int(s)
    except ValueError:
      pass
    raise ValueError(tr('INT expects an integer in a format that python accepts. Got "{value}".').format(value=s))
    # TODO: UT + test ref
  
  @classmethod
  def dumps(cls, n:int):
    if not isinstance(n, int) :
      raise TypeError(tr('INT expects an int. Got {type} (value = {value})').format(type=type(val).__name__, value=repr(val)))
      # TODO: UT + test ref
    return str(n)
  
  @classmethod
  def cast(cls, value):
    try :
      return int(value)
    except Exception as e:
      raise TypeError(tr('INT expects something castable to int. Got {type} (value = {value}). This error occured : {reason}').format(
        type=type(value).__name__,
        value=repr(value),
        reason=str(e))
      ) from e

class NUMBER(VariableType):
  @classmethod
  def loads(cls, s:str):
    try :
      return float(s)
    except ValueError:
      pass
    raise ValueError(tr('NUMBER expects a float (or int) in a format that python accepts. Got "{value}".').format(value=s))
    # TODO: UT + test ref
  
  @classmethod
  def dumps(cls, n:float):
    if not isinstance(n, float) :
      raise TypeError(tr('NUMBER expects either an int or a float. Got {type} (value = {value})').format(type=type(val).__name__, value=repr(val)))
      # TODO: UT + test ref
    return str(n)
  
  @classmethod
  def cast(cls, value):
    try :
      return float(value)
    except Exception as e:
      raise TypeError(tr('NUMBER expects something castable to float. Got {type} (value = {value}). This error occured : {reason}').format(
        type=type(value).__name__,
        value=repr(value),
        reason=str(e))
      ) from e
  
FLOAT = NUMBER


class PATH(VariableType):
  @classmethod
  def loads(cls, s:str):
    return Path(s)
  
  @classmethod
  def dumps(cls, p:Path):
    if not isinstance(p, Path) :
      raise TypeError(tr('PATH expects a Path. Got {type} (value = {value}).').format(type=type(p).__name__, value=repr(p)))
      # TODO: UT + test ref
    return str(p)
  
  @classmethod
  def cast(cls, value):
    try :
      return Path(value)
    except Exception as e:
      raise TypeError(tr('PATH expects something castable to Path. Got {type} (value = {value}). This error occured : {reason}').format(
        type=type(value).__name__,
        value=repr(value),
        reason=str(e))
      ) from e


class FILEPATH(VariableType):
  @classmethod
  def loads(cls, s:str):
    return Path(s)
  
  @classmethod
  def dumps(cls, p:Path):
    if not isinstance(p, Path) :
      raise TypeError(tr('FILEPATH expects a Path. Got {type} (value = {value}).').format(type=type(p).__name__, value=repr(p)))
      # TODO: UT + test ref
    return str(p)
  
  @classmethod
  def cast(cls, value):
    try :
      return Path(value)
    except Exception as e:
      raise TypeError(tr('FILEPATH expects something castable to Path. Got {type} (value = {value}). This error occured : {reason}').format(
        type=type(value).__name__,
        value=repr(value),
        reason=str(e))
      ) from e


class BOOL(VariableType):
  @classmethod
  def loads(cls, s:str):
    low = s.lower()
    if low in ('off', 'no', 'n', '0', 'false', 'f'):
      return False
    elif low in ('on', 'yes', 'y', '1', 'true', 't') :
      return True
    raise ValueError(tr('BOOL expects, case ignored, one of : ("on", "yes", "y", "1", "true", "t", "off", "no", "n", "0", "false", "f"). Got "{value}".').format(value=s)) 
    # TODO: UT + test ref

  @classmethod
  def dumps(cls, val:bool):
    if not isinstance(val, bool) :
      raise TypeError(tr("BOOL expects bool type. Got {type} (value = {value}).").format(type=type(val).__name__), value=repr(val))
      # TODO: UT + test ref
    return "True" if val else "False"
  
  @classmethod
  def cast(cls, value):
    try :
      return bool(value)
    except Exception as e:
      raise TypeError(tr('BOOL expects something castable to bool. Got {type} (value = {value}). This error occured : {reason}').format(
        type=type(value).__name__,
        value=repr(value),
        reason=str(e))
      ) from e

def escape(s:str, spec:str):
  # TODO: test (covered by current tests, but can silently ignore errors
  if canonical_format.get(spec) in ('cache_reference', 'build_reference', 'expanded', 'reference') :
    return cmake.escape(s)
  raise ValueError(f"Invalid format specifier '{spec}' to escape string value")


class Nil:
  pass


class Expandable(LabsObject):
  """
  May contains an expression, and can be expanded
  """
  _repr_attrs = {'_expr=': repr}
  
  def __init__(self):
    self.dep_cycle = None
    self._expr = None
    self._expanded = None

  @property
  def expr(self):
    return self._expr
  
  @expr.setter
  def expr(self, val):
    self.set_expr(Expr(val))

  def set_expr(self, expr:Expr):
    self._expr = expr or Expr()
    self.expr_changed()

  def expr_changed(self):
    self.dep_cycle = None
    self._expanded = None

  def expand(self):
    if self.expr is None :
      return ''
    else :
      return format(self.expr, 'e')

  @property
  def expanded(self):
    if self._expanded is None :
      self._expanded = self.expand()
    return self._expanded
    
class Referenceable(LabsObject):
  """
  Object possible to reference in an expression
  """
  
  # This class property holds weak refs to all instances.
  # It's primary use is to retrieve a variable from its ref in an fstring.
  instances:dict[int, weakref.ReferenceType[Variable]] = dict()
  
  def __init__(self):
    self.instances[id(self)] = weakref.ref(self)

  def __del__(self):
    del self.instances[id(self)]
    
  @classmethod
  def resolve(cls, ref:str) -> Referenceable:
    """
    resolve the reference indirection to the variable.
    """
    # TODO : better errors (dedicated class + better message)
    try :
      result = cls.instances[int(ref)]()
    except :
      raise ValueError("Not a variable ref")
    if result is None :
      raise ValueError("Variable already destroyed")
    return result

  def __add__(self, oth):
    return Expr(self) + oth

  def __radd__(self, oth):
    return oth + Expr(self)

class RecursivelyReferenceable(Expandable, Referenceable):
  """
  A referenceable that can be expanded with reference to other referenceable.
  This class implements reference cycle detection
  """
  def __init__(self):
    Expandable.__init__(self)
    Referenceable.__init__(self)

  def set_expr(self, expr:Expr):
    if cycle := self.find_cycle(expr, self):
      self.cycle_detected(expr, cycle)
    super().set_expr(expr)

  def find_cycle(self, expr:Expr|None, source) -> list[RecursivelyReferenceable]:
    if expr is None :
      return []
    for dep in ( part for part in expr.parts if isinstance(part, RecursivelyReferenceable) ):
      if dep is source :
        return [self]
      if res := dep.find_cycle(dep.expr, source) :
        res.insert(0, self)
        return res
    return []

  def cycle_detected(self, expr, cycle):
    raise VariableReferenceCycleError(f'Variable reference cycle detected assigning {self.name}', [ (rr.name if hasattr(rr, 'name') else repr(rr)) for rr in cycle ])

class CacheOutput(RecursivelyReferenceable, FormatDispatcher):
  """
  Something that is written to the cache
  """
  _repr_attrs = {'name=': str}
  def __init__(self, build:labs.LabsBuild, name:str, doc:str|list[str]):
    RecursivelyReferenceable.__init__(self)
    FormatDispatcher.__init__(self)
    self.build = build
    self.name = name
    if not isinstance(doc, list) :
      doc = [doc]
    self._doc = [ l for s in doc for l in s.split('\n') ]
    self._cache_expr = None
    
  def expr_changed(self):
    super().expr_changed()
    self._cache_expr = None

  @property
  def cache_expr(self):
    if self._cache_expr is None :
      self._cache_expr = format(self.expr, 'cr')
    return self._cache_expr
  
  def format_build_reference(self):
    return self.expanded

  @property
  def doc(self):
    return self._doc

  
class CVariable(CacheOutput):
  """
  A variable in the labs.cache.
  """
  def __init__(self, build:labs.LabsBuild, name:str, expr:Expr, doc:str):
    super().__init__(build, name, doc)
    if expr is not None :
      self.expr = expr
    self.build = build
  

class LVariable(CacheOutput):
  """
  There are these representation of a variable value / expr:

  value : python value of the variable (depends on the type)

  expr : the Expr value of the variable.

  cache_expr : a str representing the cache value assigned to the variable (Only LVariables)

  build_expr : a str representing the string assigned to the variable in the ninja.build. (only NVariables)

  expanded : The fully expanded string value, that is casted the right type to populate value.

  An LVariable can be evaluated only once. An BVariable can be reassigned.

  A CVariable is always a string, and is used in the cache to share a common value.
  """

  decl_cls:type = None # Assigned by VariableDecl

  def __init__(self, default_value, type:VariableType, doc:str, build:labs.LabsBuild, name:str):
    super().__init__(build, name, doc)
    self.default_value = default_value
    self.type = type
    self._value = Nil
  
  def expr_changed(self):
    self._value = Nil # Defensive programming if later we authorize changing the expr after on
    self.evaluate()

  def set_expr(self, expr:Expr):
    if self._value is not Nil :
      raise LVariableAlreadyEvaluatedError("Can't change the expression of {self.name} because it has already been evaluated")
    if part := next(( part for part in expr.parts if not isinstance(part, (str, CacheOutput)) ), None) :
      raise ExprTypeError(f"A {part.__class__.__name__} cannot be part of the expression of an LVariable. ({repr(part)} assigned to {repr(self)}) ")
    super().set_expr(expr)

  def cycle_detected(self, expr, cycle):
    raise VariableReferenceCycle("Can't assign `{expr}` to {self.name} because it creates a reference cycle", self.dep_cycle)
      
  @property
  def is_evaluated(self):
    return self._value is not Nil

  def evaluate(self):
    if self._expr is None :
      if isinstance(self.default_value, str) :
        self.default_value = Expr(self.default_value)
      if isinstance(self.default_value, Expr) :
        self.expr = self.default_value # evaluate() will be called again after set_expr -> expr_changed, but with Expr != None, leading to _expanded being set
      else :
        self.value = self.default_value # Using property setter to update _expr and _expanded
    else :
      self._expanded = self.expand()
      self._value = self.type.loads(self._expanded)

  @property
  def expanded(self):
    if self._expanded is None :
      self.evaluate()
    return self._expanded
  

  @property
  def value(self):
    """
    Python value of the variable. The return type depends on the variable type.
    """
    if self._value is Nil :
      self.evaluate()
    return self._value
  
  @value.setter
  def value(self, value):
    if self._value is not Nil :
      raise LVariableAlreadyEvaluatedError("Can't change the value of {self.name} because it has already been evaluated")
    self._expanded = self.type.dumps(value)
    self._expr = Expr(self._expanded)
    self._value = value
    
  @property
  def expr(self):
    if self._expr is None :
      self.evaluate()
    return self._expr
  
  @expr.setter
  def expr(self, val):
    self.set_expr(Expr(val))

  @classmethod
  def decl(cls, default_value, type:VariableType=None, doc:str=''):
    err = None
    if type is None :
      try :
        type = VariableType.typeOf(default_value)
      except TypeError as e:
        err = (LVariableTypeInferenceError, f"Can't infer the type of {{varname}}. {e.args[0]}"), e
    elif not isinstance(default_value, Expr) :
      try :
        default_value = type.cast(default_value)
      except TypeError as e:
        err = (TypeError, f'Error on assigning the default value to the variable {variable_name}. {e.args[0]}'), e
    return cls.decl_cls(default_value=default_value, type=type, doc=doc, err=err)
  

  @classmethod
  def instanciate(cls, decl, build, name):
    return cls(decl.default_value, decl.type, decl.doc, build, name)

  

class Decl(LabsObject):
  """
  Variable declaration.
  This is an helper function to distinguish variable being declared from variable existing. The build uses this distinction to cast to expression
  a variable.
  """
  
  def __init_subclass__(cls_, cls, **kwargs):
    cls_.cls = cls
    cls.decl_cls = cls_
    super().__init_subclass__(**kwargs)
  
  def __init__(self, err=None, **kwargs):
    self.err = err
    self.__dict__ |= kwargs
      

  def instanciate(self, *args, **kwargs):
    return self.cls.instanciate(self, *args, **kwargs)

class LVariableDecl(Decl, cls=LVariable):
  _repr_attrs = {'type=': repr, 'default_value=': repr}

lvariable = LVariable.decl


class Expr(LabsObject):
  """
  Expressions for LVariables and NVariables.
  Only string and variable ref concatenations are supported. This is to force all logic in labs.build,
  but still have some conveninence to repeat the value of some variables.

  @internal self.parts is a list of either string or variable references
  """
  _repr_attrs = {'self': lambda s: ', '.join( repr(p) for p in s.parts )}
  def __init__(self, *args:Expr|Expandable|str):
    self.parts = []
    for a in args :
      self += a
  
  def __iadd__(self, e:Expr|Expandable|str):
    if isinstance(e, Expandable) :
      self.parts.append(e)
    else :
      new_parts = None
      if isinstance(e, Expr) :
        if e.parts :
          new_parts = e.parts
            
      elif isinstance(e, str) :
        new_parts = self.parse_string(e)
        
      if self.parts and isinstance(self.parts[-1], str) and new_parts and isinstance(new_parts[0], str) :
        self.parts[-1] += new_parts[0]
        self.parts.extend(new_parts[1:])
      else :
        self.parts.extend(new_parts)
    return self


  def __add__(self, oth):
    result = Expr()
    result += self
    result += oth
    return result

  def __radd__(self, oth):
    result = Expr()
    result += oth
    result += self
    return result

  variable_pattern = re.compile('\\$\\(\x00([0-9]+)\\)')

  @staticmethod
  def format_part(part, spec):
    if isinstance(part, str) :
      return escape(part, spec)
    return format(part, spec)

  @classmethod
  def parse_string(cls, s:str):
    raw_parts = cls.variable_pattern.split(s)
    return [ part if not (i % 2) else Referenceable.resolve(part) for i, part in enumerate(raw_parts) ]

  def __format__(self, spec):
    return ''.join( self.format_part(part, spec) for part in self.parts )

    
  def __str__(self):
    return format(self, '')

from . import formatters
