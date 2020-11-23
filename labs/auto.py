
class Arch(object):
  """
  This class represent a machine architecture. It provides information on the architecture,
  and the wrapper (if any) to use to exec commands on it.
  """
  def __init__(self):
    raise NotImplementedError()
    

class Build(object):
  """
  This class represents a target of an auto build
  """
  def __init__(self):
    raise NotImplementedError()

class Dependency(object):
  """
  
  """
  def __init__(self):
    raise NotImplementedError()


class Toolchain(object):
  """
  This class represents a toolchain. A tool chain is a set of 



def build(*args, name, type, target_arch, build_arch):
  raise NotImplementedError()
  return Build()


def compiler(lang, name, *, target_arch, build_arch):
  raise NotImplementedError()
  

def flags(*args):
  raise NotImplementedError()



