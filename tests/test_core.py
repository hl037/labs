from pathlib import Path
from labs.core import *
import pytest

def pl(*args):
  return list(map(Path, args))

class TestFileSet:
  def assertSame(self, fs, paths, conf=None):
    paths = list(map(Path, paths))
    assert paths == fs.list
    assert set(paths) == fs.set
    if conf is not None :
      assert Dict(conf) == fs.conf

  def testConstructor(self):
    t = FileSet()
    self.assertSame(t, [])
    t = FileSet(Path('/etc/t1'))
    self.assertSame(t, [Path('/etc/t1')])
    t = FileSet('/etc/t1')
    self.assertSame(t, [Path('/etc/t1')])
    t = FileSet('/etc/t1', Path('/etc/t2'))
    self.assertSame(t, [Path('/etc/t1'), Path('/etc/t2')])
    t = FileSet('/etc/t1', [Path('/etc/t2'), '/etc/t3', '/etc/t4'], '/etc/t4')
    self.assertSame(t, [Path('/etc/t1'), Path('/etc/t2'), Path('/etc/t3'), Path('/etc/t4')])
    t2 = FileSet('/etc/t2', [Path('/etc/t3'), '/etc/t4', '/etc/t5'], '/etc/t5')
    t3 = FileSet(t, t2)
    self.assertSame(t3, [Path('/etc/t1'), Path('/etc/t2'), Path('/etc/t3'), Path('/etc/t4'), Path('/etc/t5')])
    t2 = FileSet('/etc/t2', [Path('/etc/t3'), '/etc/t4', '/etc/t5'], '/etc/t5')
    t1 = FileSet('/etc/t1', '/etc/t2', conf={'t0': 42, 't1':43})
    t2 = FileSet('/etc/t3', '/etc/t2', conf={'t1': 41, 't2':44})
    t3 = FileSet(t1, t2, conf={'tt':1337, 't0':40})
    self.assertSame(t3, ['/etc/t1', '/etc/t2', '/etc/t3'], conf={'tt':1337, 't0':40, 't1':41, 't2':44})
    t3 = FileSet(t1, t2, conf={'tt':1337, 't0':40}, import_conf=False)
    self.assertSame(t3, ['/etc/t1', '/etc/t2', '/etc/t3'], conf={'tt':1337, 't0':40})
    
  def test_len(self):
    t1 = FileSet('/etc/t1', '/etc/t2')
    t2 = FileSet('/etc/t2', '/etc/t3')
    assert 3 == len(t1 | t2)

  def test_clone(self):
    t1 = FileSet('/etc/t1', '/etc/t2')
    t2 = t1.clone()
    t2 |= '/etc/t3'
    t2.conf.ttt = 42
    self.assertSame(t1, ['/etc/t1', '/etc/t2'], conf={})
    self.assertSame(t2, ['/etc/t1', '/etc/t2', '/etc/t3'], conf={'ttt':42})

  def test_iter(self):
    fs = FileSet()
    assert [] == list(iter(fs))
    t1 = FileSet('/etc/t1', '/etc/t2')
    assert pl('/etc/t1', '/etc/t2') == list(iter(t1))

  def test___ior__(self):
    fs1 = FileSet(conf={'ttt0':42, 'ttt1':1337})
    fs1 |= '/etc/t2'
    self.assertSame(fs1, pl('/etc/t2'), conf={'ttt0':42, 'ttt1':1337})
    fs2 = FileSet('/etc/t1', conf={'ttt0':43})
    fs1 |= fs2
    self.assertSame(fs1, pl('/etc/t2', '/etc/t1'), conf={'ttt0':43, 'ttt1':1337})
    fs1 |= b'/etc/t3'
    self.assertSame(fs1, pl('/etc/t2', '/etc/t1', '/etc/t3'), conf={'ttt0':43, 'ttt1':1337})
    fs1 |= bytearray(b'/etc/t4')
    self.assertSame(fs1, pl('/etc/t2', '/etc/t1', '/etc/t3', '/etc/t4'), conf={'ttt0':43, 'ttt1':1337})
    fs1 |= Path('/etc/t5')
    self.assertSame(fs1, pl('/etc/t2', '/etc/t1', '/etc/t3', '/etc/t4', '/etc/t5'), conf={'ttt0':43, 'ttt1':1337})
    fs1 |= ['/etc/t6', '/etc/t2', '/etc/t7']
    self.assertSame(fs1, pl('/etc/t2', '/etc/t1', '/etc/t3', '/etc/t4', '/etc/t5', '/etc/t6', '/etc/t7'), conf={'ttt0':43, 'ttt1':1337})
    
  def test___or__(self):
    fs = FileSet(conf={'ttt0':42, 'ttt1':1337})
    fs1 = fs | '/etc/t2'
    self.assertSame(fs, pl(), conf={'ttt0':42, 'ttt1':1337})
    self.assertSame(fs1, pl('/etc/t2'), conf={'ttt0':42, 'ttt1':1337})
    
    fs2_ = FileSet('/etc/t1', conf={'ttt0':43})
    fs2 = fs1 | fs2_
    self.assertSame(fs1, pl('/etc/t2'), conf={'ttt0':42, 'ttt1':1337})
    self.assertSame(fs2_, pl('/etc/t1'), conf={'ttt0':43})
    self.assertSame(fs2, pl('/etc/t2', '/etc/t1'), conf={'ttt0':43, 'ttt1':1337})
    
    fs3 = fs2 | b'/etc/t3'
    self.assertSame(fs2, pl('/etc/t2', '/etc/t1'), conf={'ttt0':43, 'ttt1':1337})
    self.assertSame(fs3, pl('/etc/t2', '/etc/t1', '/etc/t3'), conf={'ttt0':43, 'ttt1':1337})
    
    fs4 = fs3 | bytearray(b'/etc/t4')
    self.assertSame(fs3, pl('/etc/t2', '/etc/t1', '/etc/t3'), conf={'ttt0':43, 'ttt1':1337})
    self.assertSame(fs4, pl('/etc/t2', '/etc/t1', '/etc/t3', '/etc/t4'), conf={'ttt0':43, 'ttt1':1337})
    
    fs5 = fs4 | Path('/etc/t5')
    self.assertSame(fs4, pl('/etc/t2', '/etc/t1', '/etc/t3', '/etc/t4'), conf={'ttt0':43, 'ttt1':1337})
    self.assertSame(fs5, pl('/etc/t2', '/etc/t1', '/etc/t3', '/etc/t4', '/etc/t5'), conf={'ttt0':43, 'ttt1':1337})
    
    fs6 = fs5 | ['/etc/t6', '/etc/t2', '/etc/t7']
    self.assertSame(fs5, pl('/etc/t2', '/etc/t1', '/etc/t3', '/etc/t4', '/etc/t5'), conf={'ttt0':43, 'ttt1':1337})
    self.assertSame(fs6, pl('/etc/t2', '/etc/t1', '/etc/t3', '/etc/t4', '/etc/t5', '/etc/t6', '/etc/t7'), conf={'ttt0':43, 'ttt1':1337})
    
  def test___ror__(self):
    fs = FileSet(conf={'ttt0':42, 'ttt1':1337})
    fs1 = '/etc/t2' | fs
    self.assertSame(fs, pl(), conf={'ttt0':42, 'ttt1':1337})
    self.assertSame(fs1, pl('/etc/t2'), conf={'ttt0':42, 'ttt1':1337})
    
    fs2_ = FileSet('/etc/t1', conf={'ttt0':43})
    fs2 = fs2_ | fs1
    self.assertSame(fs1, pl('/etc/t2'), conf={'ttt0':42, 'ttt1':1337})
    self.assertSame(fs2_, pl('/etc/t1'), conf={'ttt0':43})
    self.assertSame(fs2, pl('/etc/t1', '/etc/t2'), conf={'ttt0':42, 'ttt1':1337})
    
    fs3 = b'/etc/t3' | fs2
    self.assertSame(fs2, pl('/etc/t1', '/etc/t2'), conf={'ttt0':42, 'ttt1':1337})
    self.assertSame(fs3, pl('/etc/t3', '/etc/t1', '/etc/t2'), conf={'ttt0':42, 'ttt1':1337})
    
    fs4 = bytearray(b'/etc/t4') | fs3
    self.assertSame(fs3, pl('/etc/t3', '/etc/t1', '/etc/t2'), conf={'ttt0':42, 'ttt1':1337})
    self.assertSame(fs4, pl('/etc/t4', '/etc/t3', '/etc/t1', '/etc/t2'), conf={'ttt0':42, 'ttt1':1337})
    
    fs5 = Path('/etc/t5') | fs4
    self.assertSame(fs4, pl('/etc/t4', '/etc/t3', '/etc/t1', '/etc/t2'), conf={'ttt0':42, 'ttt1':1337})
    self.assertSame(fs5, pl('/etc/t5', '/etc/t4', '/etc/t3', '/etc/t1', '/etc/t2'), conf={'ttt0':42, 'ttt1':1337})
    
    fs6 = ['/etc/t6', '/etc/t2', '/etc/t7'] | fs5
    self.assertSame(fs5, pl('/etc/t5', '/etc/t4', '/etc/t3', '/etc/t1', '/etc/t2'), conf={'ttt0':42, 'ttt1':1337})
    self.assertSame(fs6, pl('/etc/t6', '/etc/t2', '/etc/t7', '/etc/t5', '/etc/t4', '/etc/t3', '/etc/t1'), conf={'ttt0':42, 'ttt1':1337})

  def test_filter(self):
    fs = FileSet(conf={'ttt':42})
    t_fs = fs.filter(lambda p:True)
    self.assertSame(t_fs, [], conf={'ttt':42})
    t_fs |= 't'
    t_fs.conf.tttt=43
    self.assertSame(fs, [], conf={'ttt':42})

    fs = FileSet('/etc/t1', '/etc/t2', '/etc/a/t1', conf={'ttt':42})
    t_fs = fs.filter(lambda p: p.name == 't1')
    self.assertSame(fs, ['/etc/t1', '/etc/t2', '/etc/a/t1'], conf={'ttt':42})
    self.assertSame(t_fs, ['/etc/t1', '/etc/a/t1'], conf={'ttt':42})
    t_fs |= 't'
    t_fs.conf.tttt=43
    self.assertSame(fs, ['/etc/t1', '/etc/t2', '/etc/a/t1'], conf={'ttt':42})
    
  
  def test_partition(self):
    fs = FileSet(conf={'ttt':42})
    t_fs, f_fs = fs.partition(lambda p:True)
    self.assertSame(t_fs, [], conf={'ttt':42})
    self.assertSame(f_fs, [], conf={'ttt':42})
    t_fs |= 't'
    t_fs.conf.tttt=43
    f_fs |= 'tt'
    f_fs.conf.tttt=433
    self.assertSame(fs, [], conf={'ttt':42})

    fs = FileSet('/etc/t1', '/etc/t2', '/etc/a/t1', conf={'ttt':42})
    t_fs, f_fs = fs.partition(lambda p: p.name == 't1')
    self.assertSame(fs, ['/etc/t1', '/etc/t2', '/etc/a/t1'], conf={'ttt':42})
    self.assertSame(t_fs, ['/etc/t1', '/etc/a/t1'], conf={'ttt':42})
    self.assertSame(f_fs, ['/etc/t2'], conf={'ttt':42})
    t_fs |= 't'
    t_fs.conf.tttt=43
    f_fs |= 'tt'
    f_fs.conf.tttt=433
    self.assertSame(fs, ['/etc/t1', '/etc/t2', '/etc/a/t1'], conf={'ttt':42})

  def test_filter_drop(self):
    fs = FileSet(conf={'ttt':42})
    t_fs = fs.filter_drop(lambda p:True)
    self.assertSame(t_fs, [], conf={'ttt':42})
    t_fs |= 't'
    t_fs.conf.tttt=43
    self.assertSame(fs, [], conf={'ttt':42})

    fs = FileSet('/etc/t1', '/etc/t2', '/etc/a/t1', conf={'ttt':42})
    t_fs = fs.filter_drop(lambda p: p.name == 't1')
    self.assertSame(fs, ['/etc/t2'], conf={'ttt':42})
    self.assertSame(t_fs, ['/etc/t1', '/etc/a/t1'], conf={'ttt':42})
    t_fs |= 't'
    t_fs.conf.tttt=43
    self.assertSame(fs, ['/etc/t2'], conf={'ttt':42})
    
  def test_split_types(self):
    fs = FileSet(conf={'ttt':42})
    d = fs.split_types()
    assert dict() == d

    fs = FileSet('/etc/f1.c', '/etc/f1.h', '/etc/f2.c', '/etc/f2.h', '/etc/dep.h.d', '/etc/unknown' , conf={'ttt':42})
    d = fs.split_types()
    c = {'ttt':42}
    exp = {
      'c' : ['/etc/f1.c', '/etc/f2.c'],
      'h' : ['/etc/f1.h', '/etc/f2.h'],
      'hdeps' : ['/etc/dep.h.d'],
      '_' : ['/etc/unknown'],
    }
    assert exp.keys() == d.keys()
    for k, v in exp.items() :
      self.assertSame(d[k], v, conf=c)
      
    fs = FileSet(conf={'ttt':42, 'lang':'c'})
    d = fs.split_types()
    assert dict() == d

    fs = FileSet('/etc/f1.c', '/etc/f1.h', '/etc/f2.c', '/etc/f2.h', '/etc/dep.h.d', '/etc/unknown' , conf={'ttt':42, 'lang':'c'})
    d = fs.split_types()
    c = {'ttt':42, 'lang':'c'}
    exp = {
      'c' : ['/etc/f1.c', '/etc/f1.h', '/etc/f2.c', '/etc/f2.h', '/etc/dep.h.d', '/etc/unknown'],
    }
    assert exp.keys() == d.keys()
    for k, v in exp.items() :
      self.assertSame(d[k], v, conf=c)

  def test_import_defaults(self):
    fs = FileSet()
    fs.import_defaults({})
    assert isinstance(fs.conf, Dict)
    assert {} == fs.conf

    fs = FileSet(conf={'ttt':42, 'tttt':19})
    fs.import_defaults({'ttt':43, 'tt':1337})
    assert isinstance(fs.conf, Dict)
    assert {'tt':1337, 'ttt':42, 'tttt':19} == fs.conf

  def test___contains__(self):
    fs = FileSet()
    assert '/etc/t1' not in fs
    
    fs = FileSet('/etc/t2', '/etc/t1')
    assert '/etc/t1' in fs
    assert '/etc/t2' in fs
    assert '/etc/t3' not in fs

  def test___getitem__(self):
    fs = FileSet()
    l0 = list(fs)
    l1 = [ fs[i] for i in range(len(fs)) ]
    assert l0 == l1
    
    fs = FileSet('/etc/t1')
    l0 = list(fs)
    l1 = [ fs[i] for i in range(len(fs)) ]
    assert l0 == l1
    
    fs = FileSet('/etc/t1', '/etc/t2')
    l0 = list(fs)
    l1 = [ fs[i] for i in range(len(fs)) ]
    assert l0 == l1

    fs = FileSet('/etc/t1', '/etc/t2', '/etc/t1')
    l0 = list(fs)
    l1 = [ fs[i] for i in range(len(fs)) ]
    assert l0 == l1

    fs = FileSet(['/etc/t1', '/etc/t2', '/etc/t1'])
    l0 = list(fs)
    l1 = [ fs[i] for i in range(len(fs)) ]
    assert l0 == l1

  def test___eq__(self):
    fs0 = FileSet()
    assert fs0 == fs0
    
    fs1 = FileSet()
    assert fs0 == fs1

    fs2 = FileSet(conf={'ttt':42})
    assert fs2 == fs2
    assert fs0 != fs2
    
    fs3 = FileSet(conf={'ttt':42})
    assert fs2 == fs3

    fs4 = FileSet('/etc/t1', conf={'ttt':42})
    assert fs4 == fs4
    assert fs0 != fs4
    assert fs2 != fs4

    fs5 = FileSet('/etc/t1', conf={'ttt':42})
    assert fs5 == fs4
    
    fs6 = FileSet('/etc/t1', '/etc/t2', conf={'ttt':42})
    assert fs6 == fs6
    assert fs0 != fs6
    assert fs2 != fs6
    assert fs4 != fs6

    fs7 = FileSet('/etc/t1', '/etc/t2', conf={'ttt':42})
    assert fs6 == fs7
    assert fs6 != 0

  def test_as_target(self):
    fs = FileSet()
    t = fs.as_target()
    assert t.__class__ is ninja.Target
    assert t.paths == fs.set
    
    fs = FileSet('/etc/t1')
    t = fs.as_target()
    assert t.__class__ is ninja.Target
    assert t.paths == fs.set
    
    fs = FileSet('/etc/t1', '/etc/t2')
    t = fs.as_target()
    assert t.__class__ is ninja.Target
    assert t.paths == fs.set

    fs = FileSet('/etc/t1', '/etc/t2', '/etc/t1')
    t = fs.as_target()
    assert t.__class__ is ninja.Target
    assert t.paths == fs.set

    fs = FileSet(['/etc/t1', '/etc/t2', '/etc/t1'])
    t = fs.as_target()
    assert t.__class__ is ninja.Target
    assert t.paths == fs.set

  def test_paths(self):
    fs = FileSet()
    assert fs.paths is fs.set

    fs = FileSet('/etc/t1')
    assert fs.paths is fs.set

  def test_str_sorted(self):
    fs = FileSet()
    assert [] == list(fs.str_sorted())

    fs = FileSet('/etc/t2', '/etc/t1')
    assert ['/etc/t2', '/etc/t1'] == list(fs.str_sorted())


    
    
