from labs.ninja import *
from pathlib import Path
import pytest



class TestTarget:
  def assertSame(self, t, paths):
    assert set(paths) == t.paths
    
  def test_constructor(self):
    t = Target()
    self.assertSame(t, [])
    t = Target(Path('/etc/t1'))
    self.assertSame(t, [Path('/etc/t1')])
    t = Target('/etc/t1')
    self.assertSame(t, [Path('/etc/t1')])
    t = Target('/etc/t1', Path('/etc/t2'))
    self.assertSame(t, [Path('/etc/t1'), Path('/etc/t2')])
    t = Target('/etc/t1', [Path('/etc/t2'), '/etc/t3', '/etc/t4'], '/etc/t4')
    self.assertSame(t, [Path('/etc/t1'), Path('/etc/t2'), Path('/etc/t3'), Path('/etc/t4')])
    t2 = Target('/etc/t2', [Path('/etc/t3'), '/etc/t4', '/etc/t5'], '/etc/t5')
    t3 = Target(t, t2)
    self.assertSame(t3, [Path('/etc/t1'), Path('/etc/t2'), Path('/etc/t3'), Path('/etc/t4'), Path('/etc/t5')])
    t2 = Target('/etc/t2', [Path('/etc/t3'), '/etc/t4', '/etc/t5'], '/etc/t5')

  def test_operators(self):
    t1 = Target('/etc/t1', '/etc/t2')
    t2 = Target('/etc/t2', '/etc/t3')
    t = t1 | t2
    self.assertSame(t, [Path('/etc/t1'), Path('/etc/t2'), Path('/etc/t3')])
    t = t1 & '/etc/t1'
    self.assertSame(t, [Path('/etc/t1')])
    t = '/etc/t3' | t1
    self.assertSame(t, [Path('/etc/t1'), Path('/etc/t2'), Path('/etc/t3')])
    t2 -= '/etc/t2'
    self.assertSame(t2, [Path('/etc/t3')])

  def test_len(self):
    t1 = Target('/etc/t1', '/etc/t2')
    t2 = Target('/etc/t2', '/etc/t3')
    assert 3 == len(t1 | t2)


class TestVariableAndExpr:
  def test_escape(self):
    assert 'This$ is$ an$:$\n...escaped$ str$ $${var}' == escape('This is an:\n...escaped str ${var}')

  def test_variable_str(self):
    assert '${var}' == str(Variable('var', 'val'))
    
  def test_variable_noNinja(self):
    assert 'var = val' == Variable('var', 'val').toNinja()
  
  def test_Expr_simple(self):
    assert 'This$ is$ an$:$\n...escaped$ str$ $${var}' == str(Expr(('This is an:\n...escaped str ${var}')))

  def test_Expr_add(self):
    assert 'This$ is$ an$ addition' == str(Expr('This is ') + Expr('an addition'))
    assert 'This$ is$ an$ addition' == str(Expr('This ') + (Expr('is ') + Expr('an ')) + Expr('addition'))
    
  def test_Expr_add_str(self):
    assert 'This$ is$ an$ addition' == str(Expr('This is ') + 'an addition')
    assert 'This$ is$ an$ addition' == str('This is ' + Expr('an addition'))
    assert 'This$ is$ an$ addition' == str('This ' + (Expr('is ') + 'an ') + 'addition')

  def test_Expr_variable(self):
    assert '${var}' == str(Expr(Variable('var', 'val')))
    
  def test_Expr_add_variable(self):
    assert 'This$ is$ an$ ${addition}' == str(Expr('This is an ') + Variable('addition', 'val'))
    assert '${this}$ is$ an$ addition' == str(Variable('this', 'val') + Expr(' is an addition'))
    assert '${this}$ is$ ${an}${addition}' == str(Variable('this', 'val') +(Expr(' is ') + Variable('an', 'val') ) + Expr(Variable('addition', 'val')))


class TestRule:
  def test_simple(self):
    
    res = \
'''rule r
  command = echo$ test
  b = test'''
  
    r = Rule('r', command='echo test', b='test')
    assert res == r.toNinja()

  def test_var_change(self):
    
    res = \
'''rule r
  command = echo$ test
  b = test'''
  
    r = Rule('r', command='echo test', b='te')
    r.v.b = 'test'
    assert res == r.toNinja()

  def test_cmd_raise(self):
    r = Rule('r', var='2')
    with pytest.raises(RuntimeError, match=r'Missing.*command.*') :
      r.toNinja()

class TestBuild:
  def test_simple(self):
    res = \
'''build out1 | out_imp1 : r in1 | in_imp1 || in_oo1
  imp_out = out_imp1'''
    
    r = Rule('r', command='touch '+v_out+' '+VariableRule('imp_out'))

    b = implicit('out_imp1') << Target('out1') << r.build(imp_out='out_imp1') << explicit("in1") << implicit('in_imp1') << order_only('in_oo1')

    assert res == b.toNinja().strip()
    

  def test_reversed(self):
    res = \
'''build out1 | out_imp1 : r in1 | in_imp1 || in_oo1
  imp_out = out_imp1'''
    
    r = Rule('r', command='touch '+v_out+' '+VariableRule('imp_out'))

    
    b = order_only('in_oo1') >> implicit('in_imp1') >> explicit("in1") >> r.build(imp_out='out_imp1') >> Target('out1') >> implicit('out_imp1')
    assert res == b.toNinja().strip()
    
