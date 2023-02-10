from labs import Program
from labs.core import Node, FileSet, FileType 
from labs.ninja import Expr, Target, Rule, Build
from typing import Sequence
from pathlib import Path
from functools import reduce

"""
TODO :




"""

class CompilerInput(object):
  """
  Represent a compiler input. It can be any file(s) of any language, or just some flags.
  """
  compiler_expr : Expr
  compiler_deps : Target


class LinkerInput(object):
  """
  Represent a linker input. It can be any object passed to the linker, like a dll, a static lib or a .so, or simply some flags with no file depdendencies
  """
  linker_expr : Expr
  linker_deps : Target


class Library(CompilerInput, LinkerInput):
  """
  A library represent a dependency at compiler time and link time.
  """
  pass


class Compiler(object):
  """
  Represent a compiler with all the info a CompilerNode needs
  """
  compiler_rule : Rule
  compiler_use_depfile : bool
    

class Linker(object):
  """
  Represent a linker with all the info a LinkerNode needs
  """
  linker_rule : Rule

class CompileNode(Node):
  """
  
  """
  compiler : Compiler
  compile_input : Sequence[CompilerInput]
  compile_output_base : Path

  def __init__(self, output_base:Path, compiler:Compiler, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.compiler = compiler
    self.compile_output_base = output_base
    self.compile_input = []

  def add_compile_input(self, *inp:CompilerInput):
    self.compile_input.extend(inp)

  @property
  def dep_file(self):
    return self.compile_output_base.with_suffix('.d')
  
  @property
  def output_file(self):
    return self.compile_output_base.with_suffix('.o')
  
  def preprocess(self):
    self.build = self.compiler.compiler_rule.build(
      args=reduce(lambda x, y: x + y.compiler_expr, self.compile_input),
    )
    if self.compiler.compiler_use_depfile :
      self.build.depfile = self.dep_file

    reduce(lambda build, y: y >> build, self.compile_input, self.build)

    self.build >> explicit(self.output_file)

    return FileSet(self.output_file)

  def process_(self, fs):
    fs >> self.build
    self.build.extra_flags = self

  def extra_flags(self):
    


    
class LinkNode(Node):
  """
  
  """
  linker : Linker
  link_input : Sequence[LinkerInput]
  link_output : FileSet

  def __init__(self, output:FileSet, linker:Linker, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.linker = linker
    self.link_output = output
    self.link_input = []

  def add_link_input(self, *inp:LinkerInput):
    self.link_input.extend(inp)

  def preprocess(self):
    self.build = self.linker.linker_rule.build(
      args=reduce(lambda x, y: x + y.linker_expr, self.link_input),
    )

    reduce(lambda build, y: y >> build, self.link_input, self.build)

    self.build >> explicit(self.link_output)

    return self.link_output

  def process_(self, fs):
    fs >> self.build


class Build(object):
  """
  
  """
  def __init__(self):
    



class GenericCompiler(Compiler):
  """
  
  """
  def __init__(self):
    pass

class ToolChain(object):
  """
  
  """
  def __init__(self):
    

class GCC(object):
  """
  Class for handling any gcc-like compiler toolchain.
  this include all gcc, xxx-gcc, clang and other derived.
  """
  def __init__(self):
    






