from __future__ import annotations

from enum import Enum, IntEnum
from collections import deque
import labs
from pathlib import Path
import re
import weakref

from .translation import tr
from labs.cmake import escape as escape_cache

class LVariableAlreadyEvaluatedError(RuntimeError):
  pass

class LVariableTypeInferenceError(RuntimeError):
  #TODO UT
  pass

class VariableReferenceCycle(RuntimeError):
  def __init__(self, msg, cycle):
    cycle_msg = '->'.join(cycle + [cycle[0]])
    super().__init__(f'{msg} : {cycle_msg}')
  pass


class VariableType(object):
  """
  Variable type.
  This class will hold some utils parse / print variables
  """

  @classmethod
  def loads(cls, s:str) -> str|float|Path|bool:
    raise NotImplementedError()

  @classmethod
  def dumps(cls, o:str|float|Path|bool) -> str:
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
  if spec == 'c' :
    return escape_cache(str)
  return s


class Nil:
  pass

class FormatDispatcher(object):
  """
  Implements __format__ to dispatch to format_cache, format_expanded and format_ref
  """
  def __init_subclass__(cls):
    cls._format_functions = {}
    if hasattr(cls, 'format_cache') :
      cls._format_functions['c'] = cls.format_cache
      cls._format_functions['cache'] = cls.format_cache
    if hasattr(cls, 'format_expanded') :
      cls._format_functions['e'] = cls.format_expanded
      cls._format_functions['expanded'] = cls.format_expanded
    if hasattr(cls, 'format_expanded') :
      cls._format_functions['r'] = cls.format_ref
      cls._format_functions['ref'] = cls.format_ref
      cls._format_functions['reference'] = cls.format_ref
      cls._format_functions[''] = cls.format_ref

  def __format__(self, spec):
    return self._format_functions[spec]()
      
    

class Expandable(object):
  """
  May contains an expression, and can be expanded
  """
  def __init__(self):
    self.dep_cycle = None
    self._expr = None
    self._expanded = None

  @property
  def expr(self):
    return _expr
  
  @expr.setter
  def expr(self, val):
    self.set_expr(val)

  def set_expr(self, val):
    self._expr = Expr(val)
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
    
  def format_expanded(self):
    return self.expanded


class Referenceable(object):
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

  def format_ref(self):
    return f'$(\x00{id(self)})'
    
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

  def set_expr(self, expr):
    if cycle := self.find_cycle(self):
      self.cycle_detected(expr, cycle)
    super().set_expr(expr)

  def find_cycle(self, source) -> list[RecursivelyReferenceable]:
    for dep in ( part for parts in expr if isinstance(part, RecursivelyReferenceable) ):
      if dep is source :
        return [self]
      if res := dep.find_cycle(source) :
        res.insert(0, self)
        return res
    return []

  def cycle_detected(self, expr, cycle):
    raise NotImplementedError()

class CacheOutput(RecursivelyReferenceable, FormatDispatcher):
  """
  Something that is written to the cache
  """
  def __init__(sela, build:labs.LabsBuild, name:str, doc:str|list[str]):
    super().__init__()
    self.build = build
    self.name = name
    if not isinstance(doc, list) :
      doc = [doc]
    self._doc = [ l for s in doc for l in s.split('\n') ]
    
  def expr_changed(self):
    super().expr_changed()
    self._cache_expr = None

  @property
  def cache_expr(self):
    if self._cache_expr is None :
      self._cache_expr = format(self.expr, 'c')
    return self._cache_expr
  
  def format_cache(self):
    return self.cache_expr

  @property
  def doc(self):
    return _doc

  
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


  def __init__(self, default_value, type:VariableType, doc:str, build:labs.LabsBuild, name:str):
    super().__init__(build, name, doc)
    self.default_value = default_value
    self.type = type
    self._value = Nil
  
  def expr_changed(self):
    self._value = Nil

  def set_expr(self, expr:Expr):
    if self._value is not Nil :
      raise LVariableAlreadyEvaluatedError("Can't change the expression of {self.name} because it has already been evaluated")
    super().set_expr(expr)

  def cycle_detected(self, expr, cycle):
    raise VariableReferenceCycle("Can't assign `{expr}` to {self.name} because it creates a reference cycle", self.dep_cycle)
      
  @property
  def isEvaluated(self):
    return self._value is not Nil

  def evaluate(self):
    if self.expr is None :
      if isinstance(self.default_value, Expr) :
        self.expr = self.default_value
      else :
        self.value = self.default_value # Using property setter to update _expr and _expanded
        return
    self._value = self.type.loads(self.expanded)

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
    

  @classmethod
  def decl(cls, default_value, type:VariableType=None, doc:str=''):
    return LVariableDecl(default_value, type, doc)
    

class LVariableDecl(object):
  """
  Variable declaration.
  This is an helper function to distinguish variable being declared from variable existing. The build uses this distinction to cast to expression
  a variable.
  """
  def __init__(self, default_value, type:VariableType, doc:str):
    if type is None :
      try :
        type = VariableType.typeOf(default_value)
      except TypeError as e:
        self.err = (LVariableTypeInferenceError, f"Can't infer the type of {{varname}}. {e.args[0]}"), e
      else :
        self.err = None
    else :
      self.err = None
    self.default_value = default_value
    self.type = type
    self.doc = doc

  def instanciate(self, build, name) -> LVariable:
    return LVariable(
      self.default_value,
      self.type,
      self.doc,
      build,
      name
    )

lvariable = LVariable.decl

class BVariable(Variable):
  """
  Variable appearing in the ninja build file.
  A BVariable can be evaluated several time and its value can be changed
  """
  def __init__(self, type:VariableType, doc:str, build:labs.LabsBuild, name:str):
    super().__init__('', type, doc, build, name)
    
  @property
  def build_expr(self):
    return format(self.expr, 'b')
    
    

class Expr(object):
  """
  Expressions for LVariables and NVariables.
  Only string and variable ref concatenations are supported. This is to force all logic in labs.build,
  but still have some conveninence to repeat the value of some variables.

  @internal self.parts is a list of either string or variable references
  """
  def __init__(self, *args:Expr|Variable|str):
    self.parts = []
    for a in args :
      self += a
  
  def __iadd__(self, e:Expr|Variable|str):
    if isinstance(e, Variable) :
      self.parts.append(e)
    else :
      new_parts = None
      if isinstance(e, Expr) :
        if e.parts :
          new_parts = e.parts
            
      elif isinstance(e, str) :
        new_parts = self.parseString(e)
        
      if self.parts and isinstance(self.parts[-1], str) and new_parts and isinstance(new_parts[0], str) :
        self.parts[-1] += new_parts[0]
        self.parts.extend(new_parts[1:])
      else :
        self.parts.extend(new_parts)
    return self


  def __add__(self, oth):
    breakpoint()
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

  @classmethod
  def parseString(cls, s:str):
    raw_parts = cls.variable_pattern.split(s)
    return [ part if not (i % 2) else Variable.resolve(part) for i, part in enumerate(raw_parts) ]

  def __format__(self, spec):
    return ''.join(escape(part, spec) if isinstance(part, str) else format(part, spec) for part in self.parts)

    
  def __str__(self):
    return format(self, '')

