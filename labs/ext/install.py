
from labs import Node, Dict, FileSet
from labs.ninja import *
from pathlib import Path
from labs.options import PATH
from typing import List, Sequence, Callable, Iterator, Tuple
from functools import reduce

def chain_commands_sh(*args:Expr) -> Expr:
  return reduce(lambda x, y: x + ' && ' + y, args)

class InstallPlugin(object):
  """
  Plugin to extend Install capabilities (by adding paths, etc.)
  """
  @classmethod
  def init_hook(cls, instance : 'Install'):
    """
    Called from instance.__init__(). Permits to extend an instance. 
    
    Install will call this function on the platform plugin and then on each plugin in installl_plugins.
    """
    pass
  
  @classmethod
  def preprocess_hook(cls, instance : 'Install'):
    """
    Called from instance.preprocess(). Permits to extend an instance. 
    
    Install.preprocess will call this function on the platform plugin and then on each plugin in installl_plugins.
    You can declare here ninja variables
    """
    pass

  @classmethod
  def install_gather_hook(cls, instance : 'Install') -> Callable[['Install', FileSet, Expr, Dict], None]:
    """
    Called from instance.__init__(). Permits to return an installer, e.g. a function
    installer(src:FileSet, dest:Target), constructing the rules / build to install the files into dest.
    If the install method is not supported in this host (e.g. the command does not exist), this hook should return None so that Install can test the next plugin.

    In gather mode, the files should all be installed to dest, with filesystem flatten. All paths in src are files.

    conf contains the user, group and mode

    Install will call this function on the platform plugin and then on each plugin in installl_plugins, stopping at the first not returning None. The function returned will be the one used.
    """
    pass
    
  @classmethod
  def install_recursive_hook(cls, instance : 'Install') -> Callable[['Install', FileSet, Expr, Dict], None]:
    """
    Called from instance.__init__(). Permits to return an installer, e.g. a function
    installer(src:FileSet, dest:Target), constructing the rules / build to install the files into dest.
    If the install method is not supported in this host (e.g. the command does not exist), this hook should return None so that Install can test the next plugin.

    In recursive mode, src is a directory, and its content should be copied into dest

    conf contains the user, group and mode
    
    Install will call this function on the platform plugin and then on each plugin in installl_plugins, stopping at the first not returning None. The function returned will be the one used.
    """
    pass

  @classmethod
  def install_mkdir_hook(cls, instance : 'Install') -> Callable[['Install', Target, Dict], None]:
    """
    Called from instance.__init__(). Permits to return an installer, e.g. a function
    installer(dest:Target), constructing the rules / build make to install the files into dest.
    If the install method is not supported in this host (e.g. the command does not exist), this hook should return None so that Install can test the next plugin.

    In mkdir mode, dest is the destination directory

    conf contains the user, group and mode
    
    Install will call this function on the platform plugin and then on each plugin in installl_plugins, stopping at the first not returning None. The function returned will be the one used.
    """
    pass

class InstallCmdPlugin(InstallPlugin):
  
  _conf_cbs = {
    'group' : lambda v : quote_arg_list('-g', v),
    'user' : lambda v : quote_arg_list('-o', v),
    'mode' : lambda v : quote_arg_list('-m', f'{v:03o}'),
  }

  def _get_rule_kw(self, conf):
    return { k: f(v) for k, f in self._conf_cbs.items() if (v := conf[k]) is not None }
    

  def find(_self, self:'Install'):
    if (p := getattr(self, '_InstallCmdPlugin_install_program', None)) is not None :
      return p
    p = self.find_program('install')
    self._InstallCmdPlugin_install_program = p
    self._InstallCmdPlugin_gather_rule = None
    self._InstallCmdPlugin_recursive_rule = None
    self._InstallCmdPlugin_mkdir_rule = None
    return p


  def install_gather_hook(_self, self:'Install'):
    install_p = _self.find(self)
    if not install_p.is_found :
      return
    self._InstallCmdPlugin_gather_rule = install_p.rule(
      V(mode=''), V(user=''), V(group=''), v_in, V(dest=''),
      name=self.var_prefix + 'install_gather'
    )
    return _self.gather
    
  def gather(_self, self:'Install', src:FileSet, dest:Expr, conf:Dict):
    cb = src.conf.install.rename_cb
    r = self._InstallCmdPlugin_gather_rule # type: Rule
    src >> r.build(**_self._get_rule_kw(conf), dest=dest) >> implicit([ dest + '/' + cb(p) for p in src ])
    
    
  def install_recursive_hook(_self, self:'Install'):
    install_p = _self.find(self)
    find_p = self.find_program('find')
    cd_p = self.find_program('cd')
    readlink_p = self.find_program('readlink')
    if any( (not p.is_found) for p in (cd_p, find_p, install_p, readlink_p) ):
      return
    
    inst = install_p.path
    r = self.Rule(name=self.var_prefix + 'install_recursive')
    self._InstallCmdPlugin_recursive_rule = r
    r.command = self.chain_commands(
      f'__out=`{readlink_p.path} -m '+v_out+'`',
      quote_arg_list(
        cd_p.path, v_in,
      ),
      quote_arg_list(
        find_p.path, '.', '(',
          '-type', 'd', '-exec',
            inst, r.mode, r.user, r.group, '-d', Expr('$__out/{}'),
          ';',
        ')',
        '-o', '(',
          '-type', 'f', '-exec',
            inst, r.mode, r.user, r.group, '{}', Expr('$__out/{}'),
          ';',
        ')'
      )
    )
    r << find_p << cd_p << install_p
    return _self.recursive
    
  def recursive(_self, self:'Install', src:FileSet, dest:Expr, conf:Dict):
    r = self._InstallCmdPlugin_recursive_rule # type: Rule
    src >> r.build(**_self._get_rule_kw(conf)) >> dest
  
  
  def install_mkdir_hook(_self, self:'Install'):
    install_p = _self.find(self)
    if not install_p.is_found :
      return
    
    self._InstallCmdPlugin_mkdir_rule = install_p.rule(
      V(mode=''), V(user=''), V(group=''), '-d', v_out,
      name=self.var_prefix + 'install_mkdir'
    )
    return _self.mkdir

  def mkdir(_self, self:'Install', dest:Target, conf:Dict):
    r = self._InstallCmdPlugin_mkdir_rule # type: Rule
    r.build(**_self._get_rule_kw(conf)) >> dest

install_plugins = [InstallCmdPlugin()] # type: List[InstallPlugin]



class InstallPlatformPlugin(object):
  """
  Plugin to detect the platform and return an InstallPlugin able to add the base paths
  """
  @classmethod
  def detect(cls) -> InstallPlugin:
    pass

class PlatformDetect(InstallPlatformPlugin):
  """
  Default platform plugin. You can add your own callback to PlatformDetect.detectors to extend it. 
  Your callback should take no parameter and return a tuple containing : 
    - A dict containing paths for the keys : 'PREFIX', 'BIN', 'LIB', 'INCLUDE', and 'DATA'. Or optionnaly, for eah key a tuple of (Path, Description).
    - A callback chain_commands(*cmds:Expr) -> Expr. There are common implementation provided in this module.
  """
  class Plugin(InstallPlugin):
    """
    Install plugin used by PlatformDetect. You should normally not have to instanciate or inherit this class directely.
    """
    default_paths = {
      'PREFIX' : (Path(), 'Prefix to the file system (example : home/user/.local). Will prefix all other paths (bin, usr/share, etc.)'),
      'BIN' : (Path('usr/bin'), 'Binaries location (will be installed at self.DEST / self.PREFIX / self.BIN)'),
      'LIB' : (Path('usr/lib'), 'Libraries location (will be installed at self.DEST / self.PREFIX / self.LIB)'),
      'INCLUDE' : (Path('usr/include'), 'Headerlocation (will be installed at self.DEST / self.PREFIX / self.INCLUDE)'),
      'ETC' : (Path('etc'), 'Editable text configurations location (will be installed at self.DEST / self.PREFIX / self.DATA)'),
      'DATA' : (Path('usr/share'), 'data location (will be installed at self.DEST / self.PREFIX / self.DATA)'),
      'ROOT' : (Path(), 'Root filesystem directory. You should normally not use it.'),
    }

    def __init__(self, paths:dict, chain_commands:Callable[..., Expr]):
      self.paths = paths
      self.chain_commands = chain_commands

    def init_hook(self, instance : 'Install'):
      paths = dict(self.default_paths)
      paths.update(self.paths)
      for k, v in paths.items() :
        try:
          v, d = v
        except:
          _v, d = self.default_paths[k]
        k = k.upper()
        setattr(instance, k, instance.declare_local_option( k, PATH, v, d))
      instance.chain_commands = self.chain_commands
        
    def preprocess_hook(self, instance : 'Install'):
      paths = dict(self.default_paths)
      paths.update(self.paths)
      for k in paths.keys() :
        k = k.upper()
        setattr(instance, k + '_var', instance.Variable(instance.var_prefix + k, getattr(instance, k).value))
      
  detectors = [] # type: List[Callable[[], Tuple[dict[str, Union[Tuple[Path, str], Path]], Callable[..., Expr]]]]

  @classmethod
  def detect(cls) -> InstallPlugin:
    try:
      paths, chain_commands = next( p for d in cls.detectors if (p := d()) is not None )
    except:
      return cls.Plugin({}, chain_commands_sh)
    return Plugin(paths, chain_commands)
    
install_platform_plugins = [PlatformDetect] # type: List[InstallPlatformPlugin]

def default_rename_cb(p:Path) -> str:
  return p.name

class Install(Node):
  """
  A Node to handle install targets to the right directories on the targeted platform.
  """
  def __init__(self, name='', dest=Path('/'), *args, prefix=None, **kwargs):
    super().__init__(*args, **kwargs)
    self.name = name
    self.DEST = self.declare_local_option(
      'DEST',
      PATH,
      dest,
      (
        'Destination path of the installed file (can be used by package script to set the place where the file should be actually copied).'
        'This can always been override whan calling ninja.'
      )
    )
    self.plugins = [next( p for pp in install_platform_plugins if (p := pp.detect()) is not None )] + install_plugins # type: List[InstallPlugin]
    for p in self.plugins :
      p.init_hook(self)

    self.platform_plugin = self.plugins[0]
    if prefix is not None :
      self.PREFIX.value = prefix


  def dest_expr(self, dest_type:str, sub_path:Path) -> Expr:
    return self.DEST_var + '/' +  self.PREFIX_var + '/' + getattr(self, dest_type.upper() + '_var') + (('/' + sp) if (sp := str(sub_path)) != '.' else '')
      
  @property
  def opt_prefix(self):
    return ((self.name + '_') if self.name else '') + 'INSTALL_'
  
  @property
  def var_prefix(self):
    return (self.name + '_') if self.name else ''

  def preprocess(self):
    self.DEST_var = self.Variable(self.var_prefix + 'DEST', self.DEST.value)
    for p in self.plugins :
      p.preprocess_hook(self)
      
    self.install_gather = next( inst for p in self.plugins if (inst := p.install_gather_hook(self)) is not None)
    self.install_recursive = next( inst for p in self.plugins if (inst := p.install_recursive_hook(self)) is not None)
    self.install_mkdir = next( inst for p in self.plugins if (inst := p.install_mkdir_hook(self)) is not None)

  def process_(self, fs:FileSet):
    dest_type = fs.conf.install.get('dest', 'DATA')
    sub_path = fs.conf.install.get('sub_path', self.name)
    type = fs.conf.install.get('type', 'gather')
    
    conf = dict(
      mode=fs.conf.install.get('mode', 0o755),
      user=fs.conf.install.get('user', None),
      group=fs.conf.install.get('group', None),
    )

    dest = self.dest_expr(dest_type, sub_path)
    if type == 'gather' :
      return self._process_gather(fs, dest, conf)
    if type == 'recursive' :
      assert len(fs) == 1
      return self._process_recursive(fs, dest, conf)
    if type == 'mkdir' :
      return self._process_mkdir(fs, dest, conf)
    if type == 'replicate' :
      return self._process_replicate(fs, sub_path, conf)
      

  
  def _process_gather(self, fs:FileSet, dest:Expr, conf):
    if 'rename_cb' not in fs.conf.install :
      fs.conf.install.rename_cb = default_rename_cb
    rename_cb = fs.conf.install.rename_cb
    out_target = Target([ (dest + '/' + rename_cb(p)) for p in fs ])
    self.install_gather(self, fs, dest, conf)
    return out_target

  def _process_recursive(self, fs:FileSet, dest:Expr, conf):
    out_target = Target([ (dest + '/' + p.name) for p in fs ])
    self.install_recursive(self, fs, dest, conf)
    return out_target
  
  def _process_mkdir(self, fs:FileSet, dest:Expr, conf):
    out_target = Target([ p if p.is_absolute() else (dest + p) for p in fs ])
    self.install_mkdir(self, out_target, conf)
    return out_target

  def _process_replicate(self, fs:FileSet, sub_path:Path, conf):
    base_dir = fs.conf.install.get('base_dir', self.src_dir)

    cache = {}
    for f in fs : # type: Path
      child_fs = cache.get(f.parent, None)
      if child_fs is None :
        child_fs = FileSet(conf=fs.conf, cwd=fs.cwd)
        child_fs.conf.install = Dict(child_fs.conf.install) # Avoid sharing keys
        child_fs.conf.install.type = 'gather'
        child_fs.conf.install.sub_path = sub_path / f.parent.relative_to(base_dir)
        cache[f.parent] = child_fs
      child_fs |= f
    self.add(*cache.values())
      

  @classmethod
  def apply_conf(cls, fs:FileSet, dest, sub_path, type='gather', user=None, group=None, mode=0o755):
    c = fs.conf
    if type == 'recursive' :
      assert len(fs) == 1
    c.install.user = user
    c.install.group = group
    c.install.mode = mode
    c.install.dest = dest
    if sub_path is not None :
      c.install.sub_path = Path(sub_path)
    c.install.type = type

  def add_data(self, *args, sub_path, user=None, group=None, mode=0o755):
    fs = self.FileSet(*args)
    self.apply_conf(fs, 'DATA', sub_path, type='gather', user=user, group=group, mode=mode)
    self.add(fs)

  def add_files(self, *args, dest, sub_path, user=None, group=None, mode=0o755):
    fs = self.FileSet(*args)
    self.apply_conf(fs, dest, sub_path, type='gather',  user=user, group=group, mode=mode)
    self.add(fs)
    
  def mkdir(self, *args, dest, user=None, group=None, mode=0o755):
    fs = self.FileSet(*args, cwd=Path())
    self.apply_conf(fs, dest, None, type='mkdir',  user=user, group=group, mode=mode)
    self.add(fs)

  def replicate(self, *args, base_dir, dest, sub_path, user=None, group=None, mode=0o755):
    fs = self.FileSet(*args)
    self.apply_conf(fs, dest, sub_path, type='replicate',  user=user, group=group, mode=mode)
    fs.conf.base_dir = base_dir
    self.add(fs)

  def add_dir_rec(self, arg, dest, sub_path, user=None, group=None, mode=0o755):
    fs = self.FileSet(arg)
    self.apply_conf(fs, dest, sub_path, type='recursive',  user=user, group=group, mode=mode)
    self.add(fs)
    
    



