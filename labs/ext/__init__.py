#TODO : UT

from importlib.machinery import PathFinder, SourceFileLoader, ModuleSpec
from importlib.abc import MetaPathFinder as abc_MetaPathFinder, FileLoader as abc_FileLoader
from importlib import import_module
from pathlib import Path
import sys

import labs

_prefix = 'labs.ext.'
_offset = len(_prefix)

def initExt(build: labs.LabsBuild):
  """
  Returns two lists : First, a list of paths for raw extensions, second, a list of path for extension package
  """
  root = build._internal.labs_path.parent / 'labs_ext'
  if not root.is_dir() :
    build._internal.ext_paths = None, None
  else :
    build._internal.ext_paths = [str(root)], [ str(d) for d in root.iterdir() if (d / 'setup.py').is_file() ]

def _patch_spec(fullname, spec:ModuleSpec): #loader_class, fullname, path, smsl, target):
    spec.name = fullname
    if isinstance(spec.loader, abc_FileLoader) :
      spec.loader = spec.loader.__class__(fullname, spec.loader.path)
    return spec

class _LabsExtImporter(abc_MetaPathFinder):
  """
  This class is a finder for extension of labs in the current build project.
  """
  @classmethod
  def find_spec(cls, fullname:str, path=None, target=None):
    """Try to find a spec for 'fullname' on sys.path or 'path'.

    Search only for modules starting with 'labs.ext.' and use PathFinder to first search for
    submodule in the current build, then module starting with labs_.
    """

    if not fullname.startswith(_prefix):
      return None # Not a labs extension
      
    _name = fullname[_offset:]
    if '.' in _name :
      return None # Extension already imported, this is a submodule.

    # Try importing non packaged version

    paths_1, paths_2 = labs.build._internal.ext_paths
    if paths_1 :
      spec = PathFinder.find_spec(fullname, paths_1, target)
      if spec is not None:
        return _patch_spec(fullname, spec) # Correct the module's name.
    
    # Try importing a packaged version

    installed_name = f'labs_{_name}'
    
    if paths_2 :
      spec = PathFinder.find_spec(installed_name, paths_2, target)
      if spec is not None:
        return _patch_spec(fullname, spec) # Correct the module's name.
      
    # Try importing an installed version
    
    spec = PathFinder.find_spec(installed_name, None, target)
    if spec is not None :
      return _patch_spec(fullname, spec) # Correct the module's name.
    
    return None
      
sys.meta_path.append(_LabsExtImporter())

def _clean():
  sys.modules = {
    k : v
    for k, v in sys.modules.items() if not k.startswith(_prefix)
  }
      
def __getattr__(k:str):
  if k.startswith('__'):
    raise AttributeError(k)
  import importlib
  return importlib.import_module(_prefix+k)

