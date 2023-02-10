import pytest
from labs.utils import dict2Graph, Graph


class TestGraph():
  def test_toposort_empty(self):
    g = dict2Graph({})
    assert [] == list(g.topologicalSort())

  def test_toposort_simple(self):
    g = dict2Graph({'A' : ['B'], 'B' : []})
    assert ['A', 'B'] == list(g.topologicalSort())
    
  def test_toposort_cycleError(self):
    g = dict2Graph({'A' : ['A']})
    with pytest.raises(Graph.CycleError) :
      res = g.topologicalSort()
    g = dict2Graph({'A' : ['B'], 'B' : ['A']})
    with pytest.raises(Graph.CycleError) :
      res = g.topologicalSort()
    g = dict2Graph({'A' : ['B'], 'B' : ['E', 'C'], 'C':['D'], 'D':['E', 'B'], 'E' : []})
    with pytest.raises(Graph.CycleError) :
      res = g.topologicalSort()

  def test_oposort_complex(self):
    _g = {
      'A' : ['G', 'H'],
      'B' : ['D', 'Z'],
      'C' : ['D', 'F'],
      'D' : ['E', 'Z'],
      'E' : [],
      'F' : ['B'],
      'G' : ['B', 'Z'],
      'H' : ['C', 'D', 'Z'],
      'Z' : [],
    }
    
    g = dict2Graph(_g)

    res = { n : i for i, n in enumerate(g.topologicalSort()) }
    for k, v in _g.items() :
      for l in v :
        assert res[k] < res[l]
    
  def test_oposort_complex_reverse(self):
    _g = {
      'A' : ['G', 'H'],
      'B' : ['D', 'Z'],
      'C' : ['D', 'F'],
      'D' : ['E', 'Z'],
      'E' : [],
      'F' : ['B'],
      'G' : ['B', 'Z'],
      'H' : ['C', 'D', 'Z'],
      'Z' : [],
    }
    
    g = dict2Graph(_g)

    res = { n : i for i, n in enumerate(g.topologicalSort(False)) }
    for k, v in _g.items() :
      for l in v :
        assert res[k] > res[l]
    
    


