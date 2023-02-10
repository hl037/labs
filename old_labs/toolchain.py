from .core import FileSet, FileType, Node
from labs import Rule
from .ninja import Build, Expr
import labs.runtime as lrt

from functools import cached_property, lru_cache
from typing import Callable, TypeVar

from addict import Dict
from pathlib import Path

T = TypeVar('T')

class LazyDict(dict):
  """
  Helper to provide a dict that construct the object if missing
  """

  def __getattr__(self, k):
    return self[k]

  def __missing__(self, k):
    super().__setitem__(k, self.__dict__['_factory'](k))

  def __setitem__(self):
    """
    setitem is not supported.
    """
    raise NotImplementedError()

  def _factory(self, k:str) -> T:
    """
    Object factory for missing key to reimplement
    """
    raise NotImplementedError()
    
    
class Compiler(Node):
  """
  Represent a compiler
  """
  conf : Dict
    
class Linker(Node):
  """
  Represent a linker
  """
  conf : Dict

class GenericCompiler(Compiler):
  """
  A generic compiler that should handle most of the cases
  """
  ## The ninja rule to be used by this compiler. It should have the following placeholders variables:
  ##   - $in : input files (builtin ninja variable)
  ##   - $out : output files (builtin ninja variable)
  ##   - $conf_args : configuration arguments (arguments that will be generated from the configuration)
  ##   - $raw_args : raw arguments (arguments passed in the "raw_args" entry of the configuration)
  ##   - $depfile : Where to generate the dependency file used by ninja
  rule : Rule

  ## Set to true in subclass if the compiler produces a depfile
  use_depfile : bool

  ## Language handled by this compiler. You should usually not set/change its value
  lang : str

  ## Prefix of the configuration variables. You should usually not set/change its value
  prefix : str

  ## Build that made this compiler. You should usually not set/change its value
  build : 'Build'
  
  def get_out_name(self, basename:str):
    """
    Return the name of the output from the basename (file name without extension)
    """
    return basename
  
  def get_dep_name(self, basename:str):
    """
    Return the name of the output from the basename (file name without extension)
    """
    return f'{basename}.deps'

  def parse_configuration(self, conf:Dict) -> Tuple[bool, Expr]:
    """
    Parse conf and return a tuple : (group_input, conf_args)
    """
    return (conf.get("group_input", False), Expr())

  def gather_configuration(self, fs:FileSet):
    conf = Dict()
    ac = fs.conf.all_toolchains
    if ac != {} :
      conf |= ac_conf.all | ac_conf.all_compilers | ac_conf.compilers[self.lang]
    cc = fs.conf.toolchains[self.build.toolchain.name]
    if cc != {} :
      conf |= cc_conf.all | cc_conf.all_compilers | cc_conf.compilers[self.lang]
    return self.cache_conf | conf

  def current_configuration(self) -> Dict:
    """
    Return the current configuration, gathered from the toolchain and the compiler.
    This may not be the same as the one at process time (it could ahve been modified)
    """
    return tc_conf.all | tc_conf.all_compilers | tc_conf.compilers[self.lang] | self.conf

  def preprocess(self):
    tc_conf = self.build.toolchain.conf
    self.cache_conf = self.current_configuration
    self.cache_path = self.build.path / self.lang

  def process_(self, fs:FileSet) -> Iterable[FileSet]:
    conf = self.gather_configuration(fs)
    group_input, conf_args = self.parse_configuration(conf)
    raw_args = sum(( conf.get(key, '') for key in ('raw_args_global', 'raw_args_toolchain', 'raw_args_compiler', 'raw_args') ), Expr())

    if group_input :
      out_file = self.cache_path / self.get_out_name(fs.conf.out_basename)
      fs >> self.rule.build(
        conf_args=conf_args,
        raw_args=raw_args,
      ) >> out_file
      return FileSet(out_file, conf=fs.conf, cwd=fs.cwd)
    else :
      out_dir = self.cache_path
      out_fs = FileSet(conf=fs.conf, pwd=fs.pwd)
      for fp in fs.list :
        out_file = out_dir / self.get_out_name(fp.stem)
        out_fs |= out_file
        b = (fp >> self.rule.build(
          conf_args=conf_args,
          raw_args=raw_args,
        ) >> out_file)
        if self.use_depfile :
          b.depfile=self.get_dep_name(fp.stem)
      return out_fs
    

class GenericLinker(Linker):
  """
  A generic linker that should handle object files (or other) and produce a binary (in most case)
  """
  ## The ninja rule to be used by this compiler. It should have the following placeholders variables:
  ##   - $in : input files (builtin ninja variable)
  ##   - $out : output files (builtin ninja variable)
  ##   - $conf_args : configuration arguments (arguments that will be generated from the configuration)
  ##   - $raw_args : raw arguments (arguments passed in the "raw_args" entry of the configuration)
  ##   - $depfile : Where to generate the dependency file used by ninja
  rule : Rule

  ## Set to true in subclass if the compiler produces a depfile
  use_depfile : bool

  ## Type of this linker ('shared', 'static' or 'executable')
  type : str

  ## Prefix of the configuration variables. You should usually not set/change its value
  prefix : str

  ## Build that made this linker. You should usually not set/change its value
  build : 'Build'
  
  def get_out_name(self, basename:str):
    """
    Return the name of the output from the basename (file name without extension)
    """
    return basename
  
  def get_dep_name(self, basename:str):
    """
    Return the name of the output from the basename (file name without extension)
    """
    return f'{basename}.deps'

  def parse_configuration(self, conf:Dict) -> Expr:
    """
    Parse conf and return the conf_args expression
    """
    return Expr()

  def gather_configuration(self, fs:FileSet):
    conf = Dict()
    al_conf = fs.conf.all_toolchains
    if al != {} :
      conf |= al_conf.all | al_conf.all_linkers | al_conf.linkers[self.type]
    cl_conf = fs.conf.toolchains[self.build.toolchain.name]
    if cl_conf != {} :
      conf |= cl_conf.all | cl_conf.all_linkers | cl_conf.linkers[self.type]
    return self.calhe_conf | conf

  def preprocess(self):
    tc_conf = self.build.toolchain.conf
    self.cache_conf = tc_conf.all | tc_conf.all_linkers | tc_conf.linkers[self.type] | self.conf
    self.cache_path = self.build.path
    self.all_fs = FileSet()

  def process_(self, fs:FileSet):
    self.all_fs |= fs

  def postprocess(self) -> Iterable[FileSet]:
    fs = self.all_fs
    conf = self.gather_configuration(fs)
    group_input, conf_args = self.parse_configuration(conf)
    raw_args = sum(( conf.get(key, '') for key in ('raw_args_global', 'raw_args_toolchain', 'raw_args_linker', 'raw_args') ), Expr())

    out_dir = self.cache_path
    out_fs = FileSet(conf=fs.conf, pwd=fs.pwd)
    
    out_file = self.cache_path / self.get_out_name(fs.conf.out_basename)
    fs >> self.rule.build(
      conf_args=conf_args,
      raw_args=raw_args,
    ) >> out_file
    return FileSet(out_file, conf=fs.conf, cwd=fs.cwd)
    

class Build(Node):
  """
  This class handles all the build process.
  It uses compilers and linkers to generate libraries, executables or simply raw object files.
  """

  class CompilerDict(LazyDict):
    _instance : Build
    def __init__(self, instance:Build):
      self.__dict__['_instance'] = Build

    def _factory(self, k:str) -> Compiler:
      compiler = self._instance.toolchain.new_compiler(k)

      
  class LinkerDict(LazyDict):
    _instance : Build
    def __init__(self, instance:Build):
      self.__dict__['_instance'] = Build

    def _factory(self, k:str) -> Linker:
      self._instance.toolchain.new_linker(k)
  
  toolchain : "Toolchain"
  conf : Dict
  name : str
  compilers : CompilerDict
  linkers : LinkerDict
  _link_types : set[str]

  def __init__(self, name, conf={}, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.conf = Dict(conf)
    self.compilers = CompilerDict(self)
    self.linkers = LinkerDict(self)
    self._link_types = set()

  def add_linker(self, type:str):
    linker = self.linkers[type]
    linker.conf = conf.all | conf.all_linker | conf.linkers[type] | linker.conf
    self._link_types.add(type)
    return self

  @cached_property
  def path(self):
    return self.build_dir / self.build.name





  



class Toolchain(object):
  """
  This class serves as a Build factory.
  
  Subclasses should provide Compiler_<lang> methods or nested class that return a Compiler
  (inheriting GenericCompiler is recommended). To handle special edge cases, one can also reimplement new_compiler().
  Subclasses should also provide Linker_<link_type> methods or nested class that returns a Linker (inheriting GenericLinker is recommended).
  Once again, one can reimplement new_linker() for special edge cases. link types are : 'static', 'shared' and 'executable'

  Global toolchain configuration :
  Toolchain.conf = {
    'all' : common options for all compilers and linkers
    'all_compilers' : options common to all compilers
    'all_linkers' : options common to all compilers
    'compilers' : {
      '<lang>' : Options for <lang> compilers
      ...
    }
    'linkers' : {
      '<type>' : Options for <type> linker
      ...
    }
  }
  
  The configuration aggregation for a <lang> compiler is computed like this: 
  toolchain.all | toolchain.all_compilers | toolchain.compilers.<lang> | compiler.conf | 
  fileset.conf.all_toolchains.all | fileset.all_toolchain.all_compilers | fileset.all_toolchain.compilers.<lang> |
  fileset.conf.toolchains[toolchain.name].all | fileset.conf.toolchains[toolchain.name].all_compilers | fileset.conf.toolchains[toolchain.name].compilers.<lang>
  
  The configuration aggregation for a <type> linker is computed like this: 
  toolchain.all | toolchain.all_linkers | toolchain.linkers.<type> | linker.conf | 
  fileset.conf.all_toolchains.all | fileset.all_toolchains.all_linkers | fileset.all_toolchains.linkers.<type> |
  fileset.conf.toolchains[toolchain.name].all | fileset.conf.toolchains[toolchain.name].all_linkers | fileset.conf.toolchains[toolchain.name].linkers.<type>

  For raw args, The best practice is to store in a variable the value and reference it into the raw_args_* configuration entries
  
  Options unknown to a compiler/linker are simply ignored
  """

  ## Toolchain name. Defaults be the class attribute name (or class name as fallback), followed by a unique ID.
  name : str
  
  conf : Dict

  def __init__(self, ctx=None, name=None):
    self.cache = Dict()
    if ctx is None :
      ctx = lrt.get_ctx()
    self.ctx = ctx
    if name is None :
      name = f'{getattr(self.__class__, "name", self.__class__.__name__)}_uid{self.ctx.project.unique_id()}'
    self.name = name

  def shared_library(self, *args, name, conf={}) -> Build:
    """
    Build a shared library.

    :param args: Arguments passed to build.add().
    ;param conf: Options applied to the compilers and linkers of the build at their creations. See self.build() for further informations.
    """
    return self.build(*args, name=name, conf=conf).add_linker('shared')

  def static_library(self, *args, name, conf={}) -> Build:
    """
    Build a static library.

    :param args: Arguments passed to build.add().
    :param conf: Options applied to the compilers and linkers of the build at their creations. See self.build() for further informations.
    """
    return self.build(*args, conf).add_linker('static')

  def static_and_shared_library(self, *args, name, conf={}) -> Build:
    """
    Build a static and shared library using the same object files.

    :param args: Arguments passed to build.add().
    :param conf: Options applied to the compilers and linkers of the build at their creations. See self.build() for further informations.
    """
    return self.build(*args, conf, name=name, conf=conf).add_linker('static').add_linker('shared')

  def executable(self, *args, name, conf={}) -> Build:
    """
    Build an executable.

    :param args: Arguments passed to build.add().
    :param conf: Options applied to the compilers and linkers of the build at their creations. See self.build() for further informations.
    """
    return self.executable(*args, conf).add_linker("executable")
  
  def object_files(self, *args, name=name, conf=conf) -> Build:
    """
    Build only object files that can be reused in several other builds.

    :param args: Arguments passed to build.add().
    :param conf: Options applied to the compilers and linkers of the build at their creations. See self.build() for further informations.
    """
    return self.build(*args, conf)
  
  def build(self, *args, name, conf={}) -> Build:
    """
    Build source files. By defaults, only build object files (With restricted compatibility to this toolchain, and compatible ones).
    To get a library or an executable, one should call the build.add_linker() method.

    :param args: Arguments passed to build.add().
    :param conf: Options applied to the compilers and linkers of the build at their creation. It should follow the same structure as Toolchain.conf.

    """
    conf = Dict(conf)
    build = Build(name=name, conf=conf)
    build.add(*args)

  def new_compiler(self, lang) -> Compiler:
    """
    Construct a new compiler for language lang. Defaults to call self.Compiler_<lang>. To keep the same schema, It is discouraged to reimplement this method.
    """
    factory = getattr(self, f'Compiler_{lang}', None)
    if factory is None :
      raise NotImplementedError('This toolchain ({repr(self)}) has no compiler for the language "{lang}"')
    return factory()
  
  def new_linker(self, type) -> Linker:
    """
    Construct a new linker for typeuage type. Defaults to call self.Compiler_<type>. To keep the same schema, It is discouraged to reimplement this method.
    """
    factory = getattr(self, f'Linker_{type}', None)
    if factory is None :
      raise NotImplementedError('This toolchain ({repr(self)}) has no linker for the type "{type}"')
    return factory()

  Build=Build

