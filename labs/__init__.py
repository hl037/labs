
import os
import subprocess
import shlex
import shutil
from pathlib import Path
from itertools import chain
from collections import namedtuple

from .utils import Dict

from . import ninja
from . import cmake
from .utils import Graph
from .core import *
from .options import STRING, INT, FLOAT, BOOL, PATH, FILEPATH, DeclaredOption, LazyOptions

explicit = ninja.explicit
implicit = ninja.implicit
order_only = ninja.order_only


class ProgramNotFoundError(RuntimeError):
  pass

class RuleNameConflictError(RuntimeError):
  pass

class VariablesNotInProjectError(RuntimeError):
  pass


class Rule(ninja.Rule):
  def __init__(self, project, name, rule_variables={}, **kwargs):
    kwargs.update(rule_variables)
    super().__init__(name, rule_variables=kwargs)
    object.__setattr__(self, 'project', project)
    object.__setattr__(self, 'implicit_deps', ninja.Target()) # Permit to add programs / files used by the rule automatically as implicit dep of the build

  def build(self, **kwargs):
    b = super().build(**kwargs)
    self.project << b
    return b

  def add_implicit_dep(self, o):
    self.implicit_deps |= o
  
  def __lshift__(self, o):
    try:
      o = ninja.Target(o)
      self.implicit_deps |= o
      return self
    except:
      return NotImplemented
  __rrshift__ = __lshift__


class _DefaultSpecialProgramHandler(object):
  builtin = {'cd'}

  def __call__(self, project, k):
    if k in self.builtin :
      p = Program(project, k, ...)
      p.inject_dep = lambda r:None
      return p
    return None


class Program(object):
  """
  Represent an executable
  """
  
  special_programs_handlers = [_DefaultSpecialProgramHandler()]


  def __init__(self, project, name:str, path:Path=None):
    self.project = project
    self.name = name
    self._path = path

  @property
  def is_found(self):
    return self.path is not None

  @property
  def path(self):
    return self._path if self._path != ... else self.name

  def exec(self, *args, input=None, capture=True, **kwargs):
    """
    Simple wrapper around run.
    To have more control, use run. stdin can be either a str, a bytes, or a file
    @param input : either a str, a bytes or file-like.
    @param text : set to true to use input / output in text mode
    @return (exit_code, stdout, stderr)
    """
    if self.path is None :
      raise ProgramNotFoundError(self.project, self.name)
    kw = {}
    if isinstance(input, str) :
      if not kwargs.get('text', True) :
        input = input.encode('utf8')
        kw['text'] = False
      else:
        kw['text'] = True
      kw['input'] = input
    elif isinstance(input, bytes) :
      if kwargs.get('text', False) :
        input = input.decode('utf8')
        kw['text'] = True
      else:
        kw['text'] = False
      kw['input'] = input
    else:
      kw['stdin'] = input
    kw['capture'] = capture
    kwargs.update(kw)
    if len(args) == 1 and not isinstance(args[0], str) :
      args = args[0]
    res = self.run(args, **kwargs)
    return (res.returncode, res.stdout, res.stderr)

  def run(self, *args, **kwargs):
    """
    All parameters will be forwarded to subprocess.run. To have even more flexibility to handle less
    common cases, you can use Popen().
    """
    if self.path is None :
      raise ProgramNotFoundError()
    if len(args) == 1 and not isinstance(args[0], str) :
      args = args[0]
    return subprocess.run([str(self.path), *args], **kwargs)
  
  def Popen(self, *args, **kwargs):
    """
    Lowest level function to create a process. Creates a subprocess.Popen instance with the suplied arguments.
    """
    if self.path is None :
      raise ProgramNotFoundError()
    if len(args) == 1 and not isinstance(args[0], str) :
      args = args[0]
    return subprocess.Popen([str(self.path), *args], **kwargs)

  def rule(self, *args, name=None, rule_variables={}, **kwargs):
    """
    Make a rule from the program. This has the same synthax as run or popen, but accepts ninja variables as argument too.
    However, all arguments will be shell-escaped. Thus, to use file redirection or pipes, you need to create a rule from scratch
    and thenn add the program dependencies using the stream shift operator.
    """
    if self.path is None :
      raise ProgramNotFoundError()
    if name is None :
      name = self.name
    if name in self.project.rules :
      raise ValueError(f'Un rule named {name} already exists in this project')
    if len(args) == 1 and not isinstance(args[0], str) :
      args = list(args[0])
    #kwargs['command'] = shlex.join(chain((str(self.path),), args))
    kwargs.update(rule_variables)
    if 'command' not in kwargs :
      kwargs['command'] = ninja.quote_arg_list(str(self.path), *args)
    else:
      assert len(args) == 0
    r = self >> self.project.Rule(name, rule_variables=kwargs)
    return r
  
  def variable(self, name=None):
    if name is None :
      name = f'program_{self.name}'
    v = self.project.variables.get(name, None)
    if v is not None :
      return v
    return self.project.Variable(name, str(self.path))

  def inject_dep(self, r:Rule):
    r.add_implicit_dep(self.path.resolve())

  def __rshift__(self, o):
    if isinstance(o, Rule) :
      self.inject_dep(o)
      return o
    return NotImplemented
  __rlshift__ = __rshift__
      

class _VariableProxy(object):
  """
  Proxy to change / get value of a ninja variable
  """
  def __init__(self, parent, **instance_attrs):
    _setattr = super().__setattr__
    _setattr('_parent', parent)
    for k, v in instance_attrs :
      _setattr(k, v)

  def __getattr__(self, k):
    return self._parent.variables[k].value

  def __setattr__(self, k, v):
    self._parent.variables[k] = str(value)

  def __contains__(self, k):
    return k in self._parent.variables

class _VariableProject(ninja.Variable):
  def __init__(self, name, val_cb):
    self.name = name
    self.val_cb = val_cb

  @property
  def value(self):
    return self.val_cb()

def _varDep(v:ninja.Variable):
  return ( dep for dep in v.value.value if isinstance(dep, ninja.Variable) )
  

class Project(object):
  """
  Root of a build. Each Projects intance corresponds to a ninja file.
  You should use this class to get any ninja primitives instead of instanciating them yourself.
  """
  def __init__(self, labs_path:Path, src_dir:Path, build_dir:Path, config=dict()):
    self.rules = dict()
    self.build_rules = dict()
    self.build_rules_flat = []
    self.nodes = []
    self.variables = Dict()
    self.v = _VariableProxy(self)
    self.config = Dict(config)
    self.declared_options = Dict()
    self.found_programs = dict()
    self.labs_path = labs_path
    self.src_dir = src_dir
    self.build_dir = build_dir
    self._v_src = _VariableProject('src_dir', lambda : str(self.src_dir))
    self._v_build = _VariableProject('build_dir', lambda : str(self.build_dir))
    self._v_labs = _VariableProject('labs_path', lambda : str(self.labs_path))
    self._unique_build_dir_number = 0
    self.frozen = False

  def Rule(self, name, **kwargs):
    return Rule(self, name, **kwargs)

  def Program(self, name:str, path:Path=None):
    return Program(self, name, path)

  def Variable(self, name, value):
    v = ninja.Variable(name, value)
    self.add_variable(v)
    return v

  def find_program(self, name, names=None):
    res = self.found_programs.get(name, None)
    if res :
      return res
    if names is None :
      names = (name,)
    elif isinstance(names, str) :
      names = (names,)
    res = next(( p for n in names for h in Program.special_programs_handlers if (p := h(self, n)) is not None ), None)
    if res is not None :
      return res
    for n in names :
      if isinstance(n, Path) :
        n = str(n)
      path = shutil.which(n)
      if path is not None :
        path = Path(path).resolve()
        break
    res = self.Program(name, path)
    self.found_programs[name] = res
    return res

  def unique_build_dir(self):
    res = build_dir / f'_unique_build_dir-{self._unique_build_dir_number:05d}' # type: Path
    res.mkdir(parents=True, exist_ok=True)
    return res

  def declare_option(self, name, type=STRING, default_value='', description=''):
    if (d := self.declared_options.get(name)) is None :
      d = DeclaredOption(name=name, type=type, default_value=default_value, description=description, project=self)
      if name not in self.config :
        self.config[name] = type.as_str(default_value)
      self.declared_options[name] = d
    return d
        

  @property
  def v_labs(self):
    return self._v_labs

  @property
  def v_src(self):
    return self._v_src
  
  @property
  def v_build(self):
    return self._v_build
  
  def add_rule(self, r:Rule):
    _r = self.rules.get(r.name, None)
    if _r is not None :
      if _r is not r :
        raise RuleNameConflictError('Trying to add a different rule with existing name "{r.name}"')
      return
    self.rules[r.name] = r

  def add_build(self, b:ninja.Build):
    self.add_rule(b.rule)
    for t in chain(b.explicit.o, b.implicit.o) :
      s = self.build_rules.get(t, None)
      if s is None :
        s = set()
        self.build_rules[t] = s
      s.add(b)
    self.build_rules_flat.append(b)

  def add_node(self, o:Node):
    self.nodes.append(o)

  def add_variable(self, v):
    self.variables[v.name] = v
  
  def __lshift__(self, o):
    if isinstance(o, ninja.Build) :
      self.add_build(o)
      return self
    
    if isinstance(o, ninja.Variable) :
      self.add_variable(o)
      return self

    if isinstance(o, Node) :
      self.add_node(o)
      
    return NotImplemented

  __rrshift__ = __lshift__
  add = __lshift__

  def freeze(self):
    if self.frozen :
      return
    for n in self.nodes :
      n.process()

  @property
  def ninja_preamble(self):
    return f'''
##############################
########## Preamble ##########
##############################

# This is an auto generated file by Labs (Language Agnostic Build System).
# Any modification to this file will be overwriten by subsequent call to Labs.
# The file was generated from {self.labs_path}
# for the source directory {self.src_dir}
# in the build directory {self.build_dir}.

################################################################################
'''
  ninja_sep_before_variables = '''

##############################
######### Variables  #########
##############################

'''
  ninja_sep_before_rules = '''
##############################
########### Rules  ###########
##############################

'''
  ninja_sep_before_builds = '''
##############################
########### Builds ###########
##############################

'''
  ninja_end = '''
##############################
########## The End  ##########
##############################

'''
  def writeNinja(self, f):
    self.freeze()
    f.write(self.ninja_preamble)
    f.write(self.ninja_sep_before_variables)
    sorted_vars = Graph(self.variables.values(), _varDep).topologicalSort(False)
    if len(sorted_vars) != len(self.variables) :
      raise VariablesNotInProjectError('Some variables have not been created in the project')
    v = None
    for v in sorted_vars :
      f.write(v.toNinja())
      f.write('\n')
    if v is not None :
      f.write('\n')
    f.write(self.ninja_sep_before_rules)
    for r in self.rules.values() :
      f.write(r.toNinja())
      f.write('\n\n')
    f.write(self.ninja_sep_before_builds)
    for b in self.build_rules_flat :
      other_dep = getattr(b.rule, 'implicit_deps', None)
      if other_dep :
        implicit(other_dep) >> b
      f.write(b.toNinja())
      f.write('\n\n')
    f.write(self.ninja_end)
  
  @property
  def cache_preamble(self):
    return f'''
##############################
########## Preamble ##########
##############################

# This is an auto generated file by Labs (Language Agnostic Build System).
#
# The file was generated from {self.labs_path}
# for the source directory {self.src_dir}
# in the build directory {self.build_dir}
#
# You should modify it to change build options.
# When running Labs again, a new cache will be generated considering the values of the previous.
# The sythax is the same as CMake's CMakeCache.txt :
# KEY:TYPE=VALUE
# KEY is the name of a variable in the cache.
# TYPE is a hint to GUI's for the type of VALUE, DO NOT EDIT TYPE!.
# VALUE is the current value for the KEY.

################################################################################
'''
  cache_sep_before_user_declared = '''

##############################
#### Configurable entries ####
##############################

'''
  cache_sep_before_internal = '''

##############################
###### Internal entries ######
##############################

'''
  cache_end = '''

##############################
########## The End  ##########
##############################

'''
  def writeCache(self, f):
    self.freeze()
    conf = Dict(self.config)
    f.write(self.cache_preamble)
    f.write(self.cache_sep_before_user_declared)
    keys = sorted(self.declared_options.keys())
    for k in keys :
      c = conf.pop(k)
      dc = self.declared_options[k]
      f.write(cmake.varToCache(k, c, dc.type, dc.description, dc.default_value))
      f.write('\n\n')
    f.write(self.cache_sep_before_internal)
    for c in (self.v_labs, self.v_src, self.v_build) :
      conf.pop(c.name, None)
    keys = sorted(conf.keys())
    for k in keys :
      c = conf[k]
      f.write(cmake.varToCache(k, c))
      f.write('\n\n')
    for c in (self.v_labs, self.v_src, self.v_build) :
      f.write(cmake.varToCache(c.name, c.value))
      f.write('\n\n')
    f.write(self.cache_end)



class LabsContext(object):
  """
  Context of a build file. The methods provided in this object are the global-scope functions of the build file.
  """
  def __init__(self, labs:'Labs'):
    self.labs = labs
    self.project = labs.project

  def glob(self, pattern, conf={}):
    res = self.FileSet(*self.project.src_dir.glob(pattern), conf=conf, cwd=Path(), as_is=True)
    res.cwd = self.project.src_dir
    return res
  
  def FileSet(self, *args, cwd=None, as_is=False, **kwargs):
    if cwd is None :
      _cwd = self.project.src_dir
    else:
      _cwd = cwd
    if as_is :
      res = FileSet(*args, **kwargs, cwd=Path())
      res.cwd = _cwd
      return res
    else:
      return FileSet(*args, **kwargs, cwd=_cwd)

  def getContext(self):
    return {
      'glob' : self.glob,
      'sh_esc' : shlex.quote,
      
      'Rule' : self.project.Rule,
      'Program' : self.project.Program,
      'Variable' : self.project.Variable,
      'FileSet' : self.FileSet,
      'find_program' : self.project.find_program,
      'add' : self.project.add,
      
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
      
      
      'explicit' : ninja.explicit,
      'implicit' : ninja.implicit,
      'order_only' : ninja.order_only,

      'v_command' : ninja.v_command,
      'v_depfile' : ninja.v_depfile,
      'v_deps' : ninja.v_deps,
      'v_msvc_deps_prefix' : ninja.v_msvc_deps_prefix,
      'v_description' : ninja.v_description,
      'v_dyndep' : ninja.v_dyndep,
      'v_generator' : ninja.v_generator,
      'v_in' : ninja.v_in,
      'v_in_newline' : ninja.v_in_newline,
      'v_out' : ninja.v_out,
      'v_restat' : ninja.v_restat,
      'v_rspfile' : ninja.v_rspfile,
      'v_rspfile_content' : ninja.v_rspfile_content,

      'STRING' : STRING,
      'INT' : INT,
      'FLOAT' : FLOAT,
      'BOOL' : BOOL,
      'PATH' : PATH,
      'FILEPATH' : FILEPATH,
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
    
    
    

