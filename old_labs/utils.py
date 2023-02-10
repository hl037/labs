from collections import deque, defaultdict
from addict import Dict

class DefaultDict(defaultdict):
  def __missing__(self, key):
    res = self.default_factory(key)
    self[key] = res
    return res

class Graph(object):
  class CycleError(RuntimeError):
    pass

  class Node(object):
    def __init__(self, data):
      self.data = data
      self.adj = []
      self.state = None
      
  def __init__(self, iterable, neighbors_cb):
    node = DefaultDict(lambda n: self.Node(n))
    for n in iterable :
      n_n = node[n]
      for u in neighbors_cb(n) :
        n_n.adj.append(node[u])
    self.node = node

  def topologicalSort(self, reverse = True):
    VISITED = object()
    PROCESSED = object()
    d = deque()
    s = deque()
    for n in self.node.values() :
      if n.state == None :
        s.append((False, n))
        n.state = VISITED
      while s :
        end, n = s.pop()
        if end :
          d.append(n.data)
          n.state = PROCESSED
        else:
          s.append((True, n))
          for u in n.adj :
            if u.state is PROCESSED :
              continue
            if u.state is VISITED :
              raise self.CycleError(u)
            s.append((False, u))
            u.state = VISITED
    if reverse :
      return reversed(d)
    else:
      return d
  
  
def dict2Graph(d:dict) -> Graph:
  return Graph(d.keys(), d.__getitem__)
      


