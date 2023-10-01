from __future__ import annotations

import os
import subprocess
import shlex
import shutil
from pathlib import Path
from itertools import chain
from collections import namedtuple
from threading import local as ThreadLocal
import contextlib
from typing import TYPE_CHECKING

from .utils import Dict, relativeTo
from .translation import tr

from . import cmake
from .utils import Graph
from .variables import (
  STRING,
  NUMBER,
  FLOAT,
  INT,
  BOOL,
  PATH,
  FILEPATH,
  VariableType,
  CVariable,
  LVariable,
  ExprTypeError,
  LVariableDecl,
  Expr,
  LVariableAlreadyEvaluatedError,
  LVariableTypeInferenceError,
  lvariable,
  VariableReferenceCycleError,
)

from .metabuild import (
  BVariable,
  BVariableDecl,
  GBVariable,
  LBVariable,
  LBVariableDecl,
  BRVariable,
  BRVariableDecl,
  brvariable,
  BuiltinBRVariable,
  BRule,
  BStep,
)

from .core import LabsObject, UseInternal

from icecream import ic

if TYPE_CHECKING :
  from typing import Union, IO

class CacheValueError(ValueError):
  def __init__(self, original_error:RuntimeError|str, variable:LVariable):
    self.original_error = original_error
    self.variable = variable
    super().__init__(tr('Impossible to assign {variable_name} from cache. {reason}').format(variable_name=variable.name, reason=original_error.args[0] if not isinstance(original_error, str) else original_error))

class VariableRedeclaredError(RuntimeError):
  def __init__(self, variable:LVariable):
    self.variable = variable
    super().__init__(tr('The LVariable {variable_name} has already been declared').format(variable_name=variable.name))


class LabsContext(object):
  """
  Context of a build file. Provides the locals and globals used in the build, and also takes care to sync the labs.build / labs.ctx thread-local variables
  """
  def __init__(self, build:'LabsBuild'):
    self.build = build
    self.globals = {}
    self.locals = {}


  def __enter__(self):
    self.parent = thread_local.ctx
    thread_local.ctx = self
    os.chdir(self.build._internal.build_path)
    return self

  def __exit__(self, exc_type, exc_value, traceback):
    thread_local.ctx = self.parent
    if self.parent:
      os.chdir(self.parent._internal.build_path)
    self.parent = None
    
  # old
  def getContext(self):
    return {
      'sh_esc' : shlex.quote,
      'config' : self.project.config,
      'declare_option' : self.project.declare_option,
      'src_dir' : self.project.src_dir,
      'build_dir' : self.project.build_dir,
      'unique_build_dir' : self.project.unique_build_dir,
      'labs_file' : self.project.labs_path,
      'v_labs' : self.project.v_labs,
      'v_src' : self.project.v_src,
      'v_build' : self.project.v_build,
      'v' : self.project.v,
      'variables' : self.project.variables,
    }


class LabsBuild(LabsObject, UseInternal):
  """
  Data store of the build. Holds all the variables, objects, etc.
  """

  #__slots__ = ('_internal',)
  
  class _Internal(object):
    def __init__(self, parent):
      self.cache:dict[str, Expr] = {}
      self.lvariables:dict[str, LVariable] = {}
      self.bvariables:dict[str, BVariable] = {}


  def __init__(self):
    super().__init__()

  def __getattr__(self, key:str):
    print(key)
    if res := self._internal.lvariables.get(key) :
      return res
    print(key)
    raise AttributeError(key)

  def __setattr__(self, key:str, val):
    if isinstance(val, LVariableDecl) :
      self.add_lvariable(key, val)

  def add_lvariable(self, name, default_value:LVariableDecl|Expr, type:VariableType=None, doc:str=''):
    if isinstance(default_value, LVariableDecl) :
      val = default_value
    else :
      val = LVariable.decl(default_value, type, doc)
    if isinstance(val, LVariableDecl) :
      if val.err is not None :
        (err_class, msg), from_err = val.err
        raise err_class(msg.format(varname=name)) from from_err
      if existing := self._internal.lvariables.get(name) :
        raise VariableRedeclaredError(existing)
        
      var = val.instanciate(self, name)
      self._internal.lvariables[name] = var
      cache_var = self._internal.cache.get(name)
      if cache_var :
        try :
          var.expr = cache_var.expr
        except ValueError as e:
          var._value = None
          var._expr = cache_var.expr
          var._expanded = format(cache_var.expr, 'e')
          raise CacheValueError(e, var) from e

  
  __setitem__ = __setattr__
  __getitem__ = __getattr__

  def update_cache(self, cache:dict):
    lvariables = self._internal.lvariables
    dest_cache = self._internal.cache
    for key, (value, raw_doc) in cache.items() :
      dest_cache[key] = CVariable(self, key, None, raw_doc)
    for key, (value, raw_doc) in cache.items() :
      try :
        dest_cache[key].expr = cmake.deescape(value, dest_cache.__getitem__)
      except KeyError as e:
        raise CacheValueError(f'Referenced variable `{e.args[0]}` does not exist', dest_cache[key])
      except VariableReferenceCycleError as e:
        raise CacheValueError(e, dest_cache[key])

  def write_cache(self, f:IO):
    variables = self._internal.cache
    variables.update(self._internal.lvariables)
    cmake.write_cache(f, variables)

  def writeNinja(self, f:IO):
    #TODO
    pass
    


class Labs(LabsObject):
  """
  Main class to parse labs_build.py files.
  This is the backend used by the CLI. You should normally use the CLI to build a project,
  but it may be useful to invoke it from an already running python script.

  This class configures the build object used by the build file, then processes it.
  """

  labs_filename = 'labs_build.py'
  cache_filename = 'labs_cache'
  build_filename = 'build.ninja'

  relative_path_key = 'LABS_RELATIVE_PATHS'
  src_key = 'LABS_SOURCE_PATH'

  def __init__(self, src_path:Path|str=None, build_path:Path|str=None, config=dict(), use_cache=True):
    """
    @param src_path : sources root path (path of the root directory or the build file). If a directory is passed, it will try src_path/labs_build.py
    @param build_path : build root directory
    @param config : configuration overiding the defaults and the cache.
    """
    import labs.ext as ext
    if isinstance(src_path, str) :
      src_path = Path(src_path)
    if isinstance(build_path, str) :
      build_path = Path(build_path)
    self.build = LabsBuild()
    build = self.build
    if build_path is None :
      build_path = Path.cwd().resolve()
    else:
      build_path = Path(build_path).resolve()
    
    if use_cache :
      cache_path = build_path / self.cache_filename
      if cache_path.is_file() :
        build.update_cache(self.parse_cache(cache_path))
      build.update_cache({ key: (value, []) for key, value in config.items() })

    setattr(build, self.relative_path_key, LVariable.decl(False, BOOL, doc=tr('Should paths be relatives ?')))
    relative_paths = getattr(build, self.relative_path_key).value

    if src_path :
      src_path = src_path.expanduser().resolve()
    build._internal.abs_build_path = build_path.expanduser().resolve()
    if relative_paths :
      build._internal.build_path = Path('.')
      setattr(build, self.src_key, LVariable.decl(
        relativeTo(src_path, build._internal.abs_build_path) if src_path else None,
        FILEPATH,
        doc=tr('Source directory path. labs_build.py should be in this directory.')
      ))
    else :
      build._internal.build_path = build._internal.abs_build_path
      setattr(build, self.src_key, LVariable.decl(
        src_path,
        FILEPATH,
        doc=tr('Source directory path. labs_build.py should be in this directory.')
      ))
    # From now on, build path is the correct prefix, and everything should be relative to it. src_path points to the parent of labs_build.py.
      
    src_path = getattr(build, self.src_key).value
    if src_path is None :
      raise ValueError(tr("Cannot guess the source directory path."))
    
    labs_path = src_path / self.labs_filename
    if not os.access(labs_path, os.R_OK) :
      raise OSError(tr("labs_build not fount or missing authorisations."))
    
    build._internal.src_path = src_path
    build._internal.labs_path = labs_path
    ext.initExt(build)


  @classmethod
  def parse_cache(cls, cache_path:Path):
    with cache_path.open('r') as f :
      return cmake.parse_cache(f)

  def process(self):
      
    build = self.build
    build._internal.abs_build_path.mkdir(parents=True, exist_ok=True)

    with LabsContext(build) as ctx:
      with build._internal.labs_path.open('rb') as f :
        labs_src = f.read()
      labs_code = compile(labs_src, build._internal.labs_path, 'exec')
      exec(labs_code, ctx.globals, ctx.locals)

      with (build._internal.abs_build_path/self.cache_filename).open('w') as f :
        build.write_cache(f)
      
      # with (build.abs_build_path/self.default_ninja_build_filename).open('w') as f :
      #   build.writeNinja(f)


def __getattr__(key):
  if key in ('build', 'b') :
    return thread_local.ctx.build
  if key == 'ctx' :
    return thread_local.ctx
  raise AttributeError(key)

thread_local = ThreadLocal()

thread_local.ctx = None


if TYPE_CHECKING :
  build:LabsBuild = None
  ctx:LabsBuild = None

__all__ = [
  'LVariable',
  'build',
  'ctx',
  'BOOL', 'NUMBER', 'INT', 'FLOAT', 'STRING', 'PATH', 'FILEPATH',
  'Expr',
  'Path',
  'Dict',
  'VariableRedeclaredError',
  'LVariableAlreadyEvaluatedError',
  'LVariableTypeInferenceError',
  'lvariable',
]
