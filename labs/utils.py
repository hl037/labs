from __future__ import annotations

from collections import deque, defaultdict
from addict import Dict
from pathlib import Path

class DefaultDict(defaultdict):
  def __missing__(self, key):
    res = self.default_factory(key)
    self[key] = res
    return res
  
def topological_sort(iterable, neighbors_cb, reverse=True):
  graph = Graph(iterable, neighbors_cb)
  return [ node.data for node in graph.topological_sort(reverse) ]
  
class Graph(object):
  class CycleError(RuntimeError):
    pass

  class Node(object):
    def __init__(self, data):
      self.data = data
      self.adj = []
      self.state = None
    def __repr__(self):
      return f'Node(data={repr(self.data)}, adj=[{", ".join( "Node("+repr(n.data)+")" for n in self.adj )}])'
      
  def __init__(self, iterable, neighbors_cb):
    node = DefaultDict(lambda n: self.Node(n))
    for n in iterable :
      n_n = node[n]
      for u in neighbors_cb(n) :
        n_n.adj.append(node[u])
    self.node = node

  def topological_sort(self, reverse = True):
    VISITED = "VISITED"
    PROCESSED = "PROCESSED"
    sorted_nodes = deque()
    stack = deque()
    for n in self.node.values() :
      if n.state == None :
        stack.append((False, n))
        n.state = VISITED
      while stack :
        end, n = stack.pop()
        if n.state is PROCESSED :
          continue # case when several deps appear multiple time, and have been added also multiple times to the stack.
        if end :
          sorted_nodes.append(n)
          n.state = PROCESSED
        else:
          n.state = VISITED
          stack.append((True, n))
          for u in n.adj :
            if u.state is PROCESSED :
              continue
            if u.state is VISITED :
              raise self.CycleError(u)
            stack.append((False, u))
    if reverse :
      return reversed(sorted_nodes)
    else:
      return sorted_nodes
  
  
def dict2Graph(d:dict) -> Graph:
  return Graph(d.keys(), d.__getitem__)

def relative_to(from_:Path, to:Path):
  from_ = from_.absolute()
  to = to.absolute()
  f_parts = from_.parts
  t_parts = to.parts
  common_root_len = 0
  for f, t in zip(f_parts, t_parts) :
    if f != t :
      break
    common_root_len += 1
  return Path(*(('../',) * (len(t_parts) - common_root_len)), *f_parts[common_root_len:])


