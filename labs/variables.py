from __future__ import annotations

from enum import Enum, IntEnum
import labs
from pathlib import Path

from .translation import tr

class LVariableAlreadyEvaluatedError(RuntimeError):
  pass

class LVariableTypeInferenceError(RuntimeError):
  #TODO UT
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
    elif t is int or t is float :
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
  
INT = NUMBER
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

class LVariableDirection(IntEnum):
  INPUT = 1
  OUTPUT = 2
  OVERWRITE = 3

class Nil:
  pass

class Variable(object):
  """
  Base Variable type
  """

class LVariableDecl(object):
  """
  Variable declaration.
  This is an helper function to distinguished variable being declared from variable existing. The build uses this distinction to cast to expression
  a variable.
  """
  def __init__(self, direction:LVariableDirection, default_value, type:VariableType, doc:str):
    if type is None :
      try :
        type = VariableType.typeOf(default_value)
      except TypeError as e:
        self.err = (LVariableTypeInferenceError, f"Can't infer the type of {{varname}}. {e.args[0]}"), e
      else :
        self.err = None
    else :
      self.err = None
    self.direction = direction
    self.default_value = default_value
    self.type = type
    self.doc = doc

  def instanciate(self, build, name) -> LVariable:
    return LVariable(
      self.direction,
      self.default_value,
      self.type,
      self.doc,
      build,
      name
    )

class LVariable(Variable):
  """
  Variable appearing in the LABS cache.
  An LVariable can be evaluated only once. after it is evaluated, its value can't change anymore.
  The cache is the evaluated value. NVariable are passed as ninja reference $(VAR).
  The self.expanded attribute is the one stored in the cache
  """
  def __init__(self, direction:LVariableDirection, default_value, type:VariableType, doc:str, build:labs.LabsBuild, name:str):
    self.name = name
    self.direction = direction
    self.default_value = default_value
    self.type = type
    self.doc = doc
    self._value = Nil
    self._expr = None
    self._expanded = None
    self.build = build

  @property
  def isEvaluated(self):
    return self._value is not Nil

  def evaluate(self):
    if self.isEvaluated :
      raise LVariableAlreadyEvaluatedError(self)
    if self._expr is None :
      self.value = self.default_value
    else :
      self._expr = Expr(self._expr)
      self._expanded = ''.join(
        (
          self.build[part.name].expanded
          if isinstance(part, LVariableRef) else
          part.ninja_ref
          if isinstance(part, NVariableRef) else
          part
        )
        for part in self._expr.parts
      )
      self._value = self.type.loads(self._expanded)

  @property
  def value(self):
    if self._value is Nil :
      self.evaluate()
    return self._value
  
  @property
  def expanded(self):
    if self._value is Nil :
      self.evaluate()
    return self._expanded
  
  @value.setter
  def value(self, value):
    if self.isEvaluated :
      raise LVariableAlreadyEvaluated(self)
    # Note : this order is important so that an expression is raised before the value is assigned if incompatible value
    self._expanded = self.type.dumps(value)
    self._expr = Expr(self._expanded)
    self._value = value

  @property
  def expr(self):
    return self._expr
  
  @expr.setter
  def expr(self, value):
    ## TODO check no ref from another build
    if self.isEvaluated :
      raise LVariableAlreadyEvaluated(self)
    self._expr = Expr(value) if value is not None else None

  @classmethod
  def I(cls, default_value, type:VariableType=None, doc:str=''):
    return LVariableDecl(LVariableDirection.INPUT, default_value, type, doc)
    
  @classmethod
  def O(cls, default_value, type:VariableType=None, doc:str=''):
    return LVariableDecl(LVariableDirection.OUTPUT, default_value, type, doc)
    
  @classmethod
  def IO(cls, default_value, type:VariableType=None, doc:str=''):
    return LVariableDecl(LVariableDirection.OVERWRITE, default_value, type, doc)
  
  
class VariableRef(object):
  """
  A reference to a variable
  """
  def __init__(self, var:Variable):
    self.name = var.name
    # TODO add flag LVariable or NVariable etc.

class LVariableRef(VariableRef):
  """
  A reference to a LVariable
  """
  pass

class NVariableRef(VariableRef):
  """
  A reference to a NVariable
  """
  @property
  def ninja_ref(self):
    return f'$({self.name})'
    

class Expr(object):
  """
  Expressions for LVariables and NVariables.
  Only string and variable ref concatenations are supported. This to force all logic in labs.build,
  but still have some conveninence to repeat the value of some variables.

  @internal self.parts is a list of either string or variable references
  """
  def __init__(self, *args:Expr|str):
    # TODO support variable refs
    self.parts = []
    isLastPartStr = False
    for a in args :
      if isinstance(a, VariableRef) :
        self.parts.append(a)
        # TODO add flags to detect LVar ref and NVar ref recursively
      else :
        new_parts = None
        if isinstance(a, Expr) :
          if a.parts :
            new_parts = a.parts
        elif isinstance(a, str) :
          new_parts = self.parseString(a)
        if new_parts :
          if isLastPartStr and isinstance(a.parts[0], str) :
            self.parts[-1] += new_parts[0]
            self.parts.extend(new_parts[1:])
          else :
            self.parts.extend(new_parts)
          isLastPartStr = isinstance(self.parts[-1], str)

  def parseString(self, s:str):
    # TODO
    return s

    
  def __str__(self):
    return ''.join(map(str, self.parts))

