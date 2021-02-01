"""

This module is about the high-level interface to ninja, and are the core concepts of LABS.

Everythin is articulated around the Toolchain concept. A toolchain is analog to a set of %.ext make rules : it defines for each type of file a Compiler.

A Compiler knows how to translate a set of file of the type it supports as input to other file of another 
"""

import operator
from pathlib import Path
from collections import deque
from functools import reduce, cached_property
from .utils import Dict, DefaultDict
from . import ninja
import labs.runtime as lrt
from labs.options import DeclaredOption

from typing import Sequence, Union, Iterable, Union, Any

class FileTypeNotFound(RuntimeError):
  pass

class NodeIsFrozen(RuntimeError):
  pass

class FileType(object):
  """
  A File type
  """
  filetypes = []

  def __init__(self, name, aliases, description=''):
    self.name = name
    self.aliases = aliases

  def __contains__(self, filename:Any):
    name = str(filename)
    return any( name.endswith(f'.{suffix}') for suffix in self.aliases )
  
  @classmethod
  def addFileType(cls, name, aliases):
    ft = cls(name, aliases)
    cls.filetypes.append(ft)
    for a in aliases :
      setattr(cls, a, ft)

  @classmethod
  def get(cls, filename:Any):
    name = str(filename)
    try:
      return next( ft for ft in cls.filetypes if name in ft) 
    except StopIteration:
      raise FileTypeNotFound(f'File type not found for filename {repr(filename)}')

  @classmethod
  def __getitem__(cls, k):
    return getattr(cls, k)


    
FileType.addFileType('h', ('h',))
FileType.addFileType('hpp', ('hpp', 'H', 'h++', 'hxx',))
FileType.addFileType('c', ('c',))
FileType.addFileType('cpp', ('cpp', 'C', 'c++', 'cxx',))
FileType.addFileType('hdeps', ('h.d', 'hpp.d', 'H.d', 'h++.d', 'hxx.d', 'c.d', 'cpp.d', 'C.d', 'c++.d', 'cxx.d',))
FileType.addFileType('d', ('d',))
FileType.addFileType('o', ('o',))
FileType.addFileType('so', ('so',))
FileType.addFileType('exe', ('exe',))
FileType.addFileType('a', ('a',))



class FileSet(ninja.Target):
  """
  Set of input files
  """
  list : list[Path]
  set : set[Path]

  def __init__(self, *args, conf:Dict=None, import_conf=True, cwd=Path()):
    if len(args) == 1 :
      a, = args
      if isinstance(a, FileSet) and conf is None:
        self.list = list(a.list)
        self.set = set(a.set)
        self.conf = Dict(a.conf)
        self.cwd = a.cwd
        return
    self.set = set()
    self.list = []
    self.conf = Dict()
    self.cwd = cwd
    for a in args :
      self |= a
    if not import_conf :
      self.conf = Dict()
    if conf is not None :
      self.conf |= conf

  def clone(self):
    return FileSet(self)

  def __iter__(self):
    return iter(self.list)

  def __ior__(self, oth):
    if isinstance(oth, (bytes, bytearray)) :
      oth = oth.decode('utf8'),
    elif isinstance(oth, (str, Path)) :
      oth = oth,
    elif isinstance(oth, FileSet) :
      self.conf |= oth.conf
    for a in oth :
      p = self.cwd / a # if a is absolute, result will be a
      if p not in self.set :
        self.set.add(p)
        self.list.append(p)
    return self

  def __or__(self, oth):
    res = FileSet(self)
    res |= oth
    return res

  def __ror__(self, oth):
    res = FileSet(oth, cwd=self.cwd)
    res |= self
    return res

  def filter(self, pred):
    res = FileSet(cwd=self.cwd)
    res.list = [ a for a in self if pred(a) ]
    res.set = set(res.list)
    res.conf = Dict(self.conf)
    return res

  def partition(self, pred):
    true_set, false_set = FileSet(cwd=self.cwd), FileSet(cwd=self.cwd)
    pred = [ pred(a) for a in self ]
    true_set.list = [ a for a, p in zip(self, pred) if p ]
    false_set.list = [ a for a, p in zip(self, pred) if not p ]
    true_set.set = set(true_set.list)
    false_set.set = set(false_set.list)
    true_set.conf = Dict(self.conf)
    false_set.conf = Dict(self.conf)
    return true_set, false_set

  def filter_drop(self, pred):
    true_set = FileSet(cwd=self.cwd)
    pred = [ pred(a) for a in self ]
    true_set.list = [ a for a, p in zip(self, pred) if p ]
    self.list = [ a for a, p in zip(self, pred) if not p ]
    true_set.set = set(true_set.list)
    self.set = set(self.list)
    true_set.conf = Dict(self.conf)
    return true_set

  def split_types(self):
    res = Dict()
    if 'lang' in self.conf :
      if not self.list :
        return res
      res[self.conf.lang] = self.clone()
      return res
    _d = DefaultDict(lambda k: [])

    for p in self.list :
      try:
        _d[FileType.get(p).name].append(p)
      except:
        _d['_'].append(p)
    for k, l in _d.items() :
      fs = FileSet(cwd=self.cwd)
      fs.list = l
      fs.set = set(l)
      fs.conf = Dict(self.conf)
      res[k] = fs
    return res

  def import_defaults(self, conf):
    nc = Dict(conf)
    nc |= self.conf
    self.conf = nc

  def __len__(self):
    return len(self.list)

  def __contains__(self, a):
    a = Path(a)
    return a in self.set

  def __getitem__(self, n) -> Path:
    return self.list[n]

  def __eq__(self, oth):
    if not isinstance(oth, FileSet) :
      return False
    return self.list == oth.list and self.conf == oth.conf


  def as_target(self) -> ninja.Target:
    """
    This method should be called only for optimization, since FileSet can act as a ninja.Target.
    Another case is to be able to use the & and the ^ operators on the set.
    """
    res = ninja.Target()
    res.paths = set(self.set)
    return res
  
  @property
  def paths(self):
    return self.set

  def str_sorted(self):
    return map(str, self.list)

  def ni(self): # pragma: no cover
    return NotImplemented

  __and__ = ni
  __rand__ = ni
  __iand__ = ni

  __xor__ = ni
  __rxor__ = ni
  __ixor__ = ni
  
  __sub__ = ni
  __rsub__ = ni
  __isub__ = ni

  del ni




class Node(object):
  """
  Base class for a node in a toolchain.
  """

  def __init__(self, ctx=None):
    self._frozen = False
    self._processing = False
    self._input = deque()
    self._output = deque()
    if ctx is None :
      ctx = lrt.get_ctx()
    self.ctx = ctx
    self._ctx = ctx.getContext()
    self.project = ctx.project
    self.project.add(self)
    self.dependencies = []

  def __getattr__(self, k):
    try:
      return self._ctx[k]
    except KeyError as e:
      raise AttributeError(k) from e

  def declare_local_option(self, name, *args, **kwargs) -> DeclaredOption:
    """
    Declare an option local to this node (self.opt_prefix and self.name will be prefixed to the option name)
    """
    name = getattr(self, self.opt_prefix, '') + name
    return self.declare_option(name, *args, **kwargs)

  def add(self, *dependencies:Union[ninja.Target, FileSet, 'Node']):
    """
    Add a file set to the input of the node. This function should normally not be reimplemented in subclass
    """
    if self._frozen :
      raise NodeIsFrozenError()
    if self._processing :
      self._input.extendleft(reversed(dependencies))
      return
    for dep in dependencies :
      if isinstance(dep, Node) :
        self._input.append(Node)
        continue
      if isinstance(dep, ninja.Expr) :
        dep = ninja.Target(dep)
      if not isinstance(dep, (FileSet, ninja.Target)) :
        dep = self.FileSet(dep)
      self._input.append(dep)

  def preprocess(self) -> Iterable[Union[FileSet, ninja.Target]]:
    """
    Called when the processing of the node starts. Overide this hook when you want to do some preprocessing knowing the node is about to be processed.
    Note : the self._processing flag will still be False in this node. Thus, you can call self.add(...) to add some input to be processed at the end.
    
    @return Collection of FileSet that should be added to the output.
    """
    pass

  def postprocess(self) -> Iterable[Union[FileSet, ninja.Target]]:
    """
    Called when all the input have been processed. Overiding this hook permits to add additionnal rules and output,
    for example from the processing of an additional nodes that would have gathered input from the process_* functions.
    Note : the self._frozen will be set to True thus you won't be able to call self.add() in this method.
    
    @return Collection of FileSet that should be added to the output.
    """
    pass
      
  def _extend_output(self, outs):
    if outs is None :
      return
    self._output.extend(outs)

  def process(self):
    """
    Process the node. It will call all self.process_* function on each inputs.
    These methods should return an iterable of the output to add, and can call self.add() to reinject other sources.
    """
    if self._frozen :
      return
    if self._processing :
      raise RecursionError('Already processing this node. Check for recursive Node dependency ?')
    self._extend_output(self.preprocess())
    self._processing = True
    while self._input :
      dep = self._input.popleft()
      if isinstance(dep, Node) :
        self.add(*dep.output)
      elif isinstance(dep, FileSet) :
        for lang, fs in dep.split_types().items() :
          self._extend_output(
            getattr(self, f'process_{lang}', self.process_)(fs)
          )
      elif isinstance(dep, ninja.Target) :
        self._extend_output(self.process_target(dep))
      else:
        ValueError(f'This node type is not ({self.__class__.__name__}) is not able to process ({dep.__class__.__name__}) type')
    self._frozen = True
    self._extend_output(self.postprocess())
  
  def process_target(self, tar) -> Iterable[Union[FileSet, ninja.Target]]:
    """
    Process function for raw Target inputs. The default behavior is to raise a ValueError, since this is an edge case to support dynamic targets, and except for some special use cases, it is prefered to only manipulate FileSet.
    """
    raise ValueError(f'This node type ({self.__class__.__name__}) is not able to process raw Target input')

  def process_(self, fs:FileSet) -> Iterable[Union[FileSet, ninja.Target]]:
    """
    Default process function. The default raise an error saying the node is not able to process this file type.
    Any input added through self.add() will be processed immediately after this node, in Last added first processed order.
    """
    raise ValueError(f'This node type ({self.__class__.__name__}) is not able to process "{fs.conf.lang}" file type')
  
  @cached_property
  def output(self) -> Iterable[Union[FileSet, ninja.Target]]:
    """
    Freeze the node and get its output
    """
    self.process()
    return self._output























# class Atom():
#   """
#   Base class of Stream, Option and Flag. It can also simply be an expression.
#   """
#   def __init__(self, expr):
#     self.expr = expr
# 
#   def getExpr(self, ctx):
#     return expr
# 
#   def __and__(self, oth):
#     if isinstance(oth, Stream) :
#       return oth.__rand__(self)
#     if isinstance(oth, Atom) :
#       return Stream(self, oth)
#     return super().__and__(oth)
# 
#   def __rand__(self, oth):
#     if isinstance(oth, Atom) :
#       return Stream(oth, self)
#     return super().__rand__(oth)
#     
#       
# 
# class Stream(Atom):
#   """
#   A stream is a list of Atom
#   """
#   def __init__(self, *args):
#     self.atoms = list(args)
#   
#   def getExpr(self, ctx):
#     return reduce(operator.add, ( x.getExpr(ctx) for x in self.atoms ))
#   
#   def __and__(self, oth):
#     if isinstance(oth, Stream) :
#       return Stream(*self.atoms, *oth.atoms)
#     if isinstance(oth, Atom) :
#       return Stream(*self.atoms, oth)
#     return super().__and__(oth)
# 
#   def __rand__(self, oth):
#     if isinstance(oth, Atom) :
#       return Stream(oth, *self.atoms)
#     return super().__rand__(oth)
#   
# 
# class Flag(Atom):
#   """
#   A flag is a low level abstraction of the expression, with elements that can be placed either before or after an atom.
#   """
#   def __init__(self, on_atom:Union[Atom, Flag], off_atom:Union[Atom, None]=None):
#     if off_atom is None :
#       assert isinstance(on_atom, Flag)
#       self.on_atom = on_atom.on_atom
#       self.off_atom = on_atom.off_atom
#     else:
#       self.on_atom = on_atom
#       self.off_atom = off_atom
# 
#   def getExpr(self, ctx):
#     return self.on_atom.getExpr(ctx)
# 
#   def __call__(self, atom):
#     return FlagWrapped(self, atom)
# 
#   def __neg__(self):
#     return NotOff(self)
# 
# class FlagWrapped(Atom):
#   """
#   An atom wrapped by a flag
#   """
#   def __init__(self, flag:Flag, atom:Atom):
#     self.flag = flag
#     self.atom = atom
# 
#   def getExpr(self, ctx):
#     return self.flag.on_atom.getExpr(ctx) + self.atom.getExpr(ctx) + self.flag.off_atom.getExpr(ctx)
# 
# class OffFlag(Flag):
#   """
#   A reversed flag
#   """
#   def __init__(self, flag:Flag):
#     self.flag = flag
# 
#   @property
#   def on_atom(self):
#     return self.flag.off_atom
# 
#   @property
#   def off_atom(self):
#     return self.flag.on_atom
# 
#   def __neg__(self):
#     return self.flag
#   __invert__ = __neg__
# 
# 
# class Options(Atom):
#   """
#   An option is an abstraction of the flags : it is an atempt at provinding an unified API for all compilers. This way a compiler can treat or not an option if it recognise it.
#   """
#   def __init__(self, options):
#     self.options = Dict(options)
# 
#   def __or__(self, oth:Options):
#     if not isinstance(oth, Options) :
#       return NotImplemented
#     res = Options(self.options)
#     res |= oth
#     return res
# 
#   def __ior__(self, oth:Options):
#     if not isinstance(oth, Options) :
#       return NotImplemented
#     for k, v in oth.options.items() :
#       if k in self.options :
#         self.options[k] |= v
#       else :
#         self.options[k] = v
# 
#   def getExpr(self, ctx):
#     return ctx.compiler.getOptionsExpr(ctx, self)
# 
# class OptionsWrapped(Atom):
#   """
#   An atom wrapped by an Options
#   """
#   def __init__(self, options:Options, atom:Atom):
#     self.options = options
#     self.atom = atom
#     
#   def getExpr(self, ctx):
#     return ctx.compiler.getOptionsWrappedExpr(ctx, self)
# 
# def Option(name, **kwargs):
#   return Options({name:Dict(kwargs)})
# 
# 
# class Target(Atom, ninja.Target):
#   def getExpr(self, ctx):
#     return ctx.compiler.getTargetExpr(ctx, self)
# 
# 
# 
# 
# class Compiler(object):
#   """
#   A compiler takes files of specific types and produce files from another types
#   """
#   def __init__(self, in_types, out_types):
#     self.in_types = in_types
#     self.out_types = out_types
# 
# class Toolchain(object):
#   """
#   A  Toolchain stores compiler for each file type and is able to reconstruct a graph of the global step to produce a build.
#   """
#   def __init__(self):
#     self.compiler = Dict()
#     
    
