
import os
import subprocess
import shlex
import shutil
from pathlib import Path
from itertools import chain
from collections import namedtuple

from .utils import Dict

from . import cmake
from .utils import Graph
from .variables import STRING, INT, FLOAT, BOOL, PATH, FILEPATH


class Project(object):
  """
  Root of a build. Each Projects intance corresponds to a ninja file.
  You should use this class to get any ninja primitives instead of instanciating them yourself.
  """

class LabsContext(object):
  """
  Context of a build file. The methods provided in this object are the global-scope functions of the build file.
  """
  def __init__(self, labs:'Labs'):
    self.labs = labs
    self.project = labs.project
    
  def __init__(self, labs_path:Path, src_dir:Path, build_dir:Path, config=dict()):
    self.labs_path = labs_path
    self.src_dir = src_dir
    self.build_dir = build_dir
    self.config = Dict(config)

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




class Labs(object):
  default_labs_filename = 'labs_build.py'
  default_cache_filename = 'labs_cache'
  default_ninja_build_filename = 'build.ninja'

  absolute_path_key = '__LABS_ABSPATH'
  relative_path_key = '__LABS_RELPATH'

  """
  Main class to parse labs_build.py files.
  This is the backend used by the CLI. You should normally use the CLI to build a project,
  but it may be useful to invoke it from an already running python script.
  """
  def __init__(self, src_path=None, build_path=None, config=dict(), use_cache=True):
    """
    @param src_path : sources root path (path of the root directory or the build file). If a directory is passed, it will try src_path/labs_build.py
    @param build_path : build root directory
    @param config : configuration overiding the defaults and the cache.
    """
    if build_path is None :
      self.build_path = Path.cwd().resolve()
    else:
      self.build_path = Path(build_path).resolve()
    self.override_config = config
    
    config = Dict()
    
    if use_cache :
      cache_path = self.build_path / self.default_cache_filename
      if cache_path.is_file() :
        config.update(self.parse_cache(cache_path))

    if src_path is None :
      src_path = config.get('labs_path', None)
      if src_path is None :
        raise ValueError("Cannot guess the source directory path")
    
    config.update(self.override_config)
    
    self.src_path = Path(src_path).resolve()
    if self.src_path.is_dir() :
      self.labs_path = self.src_path/self.default_labs_filename
    elif self.src_path.is_file() :
      self.labs_path = self.src_path
      self.src_path = self.src_path.parent

    if not os.access(self.labs_path, os.R_OK) :
      raise OSError("labs_build not fount or missing authorisations")

    if cmake.str2bool(config.get(self.absolute_path_key, True)) :
      self.labs_path = self.labs_path.absolute()
      self.src_path = self.src_path.absolute()
      self.build_path = self.build_path.absolute()
    elif cmake.str2bool(config.get(self.relative_path_key, False)) :
      cwd = Path.cwd().absolute()
      self.labs_path = Path(os.path.relpath(self.labs_path, cwd))
      self.src_path = Path(os.path.relpath(self.src_path, cwd))
      self.build_path = Path(os.path.relpath(self.build_path, cwd))

    self.project = Project(self.labs_path, self.src_path, self.build_path, config)

  @classmethod
  def parse_cache(cls, cache_path:Path):
    with cache_path.open('r') as f :
      return cmake.parse_cache(f)

  def process(self):
    import labs.ext as ext
    import labs.runtime as runtime
    
    self.build_path.mkdir(parents=True, exist_ok=True)
    
    with self.labs_path.open('rb') as f :
      labs_src = f.read()
    labs_code = compile(labs_src, self.labs_path, 'exec')

    try:
      ctx = LabsContext(self)
      runtime._ctx = ctx

      _locals = dict()
      exec(labs_code, ctx.getContext(), _locals)

      with (self.build_path/self.default_ninja_build_filename).open('w') as f :
        self.project.writeNinja(f)

      with (self.build_path/self.default_cache_filename).open('w') as f :
        self.project.writeCache(f)
    finally:
      ext._clean()
      runtime._ctx = None
    
    
    

