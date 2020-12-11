from labs import *
from pathlib import Path
from unittest.mock import Mock
from subprocess import CompletedProcess
import pytest
import shutil
from io import StringIO


@pytest.fixture
def project():
  return Project(Path('/test'), Path('/test'), Path('/test'))

@pytest.fixture
def prog(project):
  return Program(project, 'echo_cmd', Path('echo'))

@pytest.fixture
def mock_subprocess(monkeypatch):
  ret_run = CompletedProcess(['arg0', 'arg1', 'arg3'], 42, 'res_stdout', 'res_stderr')
  ret_popen = object()
  mock_run = Mock(return_value=ret_run)
  mock_popen = Mock(return_value=ret_popen)
  monkeypatch.setattr('subprocess.run', mock_run)
  monkeypatch.setattr('subprocess.Popen', mock_popen)
  return mock_run, mock_popen, ret_run, ret_popen


class TestProgram:
  def test_find_program_name(self, project:Project):
    p = project.find_program('echo')
    assert str(p.path) == shutil.which('echo')
    assert p.name == 'echo'
    assert p.is_found
    
  def test_find_program_names(self, project:Project):
    p = project.find_program('echo_cmd', 'echo')
    assert str(p.path) == shutil.which('echo')
    assert p.name == 'echo_cmd'
    assert p.is_found
    
  def test_find_program_names_multi(self, project:Project):
    p = project.find_program('echo_cmd', ('echo', 'a_random_name_that_wont_be_matched'))
    assert str(p.path) == shutil.which('echo')
    assert p.name == 'echo_cmd'
    assert p.is_found
    
    p = project.find_program('echo_cmd', ('a_random_name_that_wont_be_matched', 'echo'))
    assert str(p.path) == shutil.which('echo')
    assert p.name == 'echo_cmd'
    assert p.is_found
    
  def test_find_programm_notfound(self, project:Project):
    p = project.find_program('echo_cmd', 'a_random_name_that_wont_be_matched')
    assert p.path is None
    assert p.name == 'echo_cmd'
    assert not p.is_found

    p = project.find_program('echo_cmd', ('a_random_name_that_wont_be_matched',))
    assert p.path is None
    assert p.name == 'echo_cmd'
    assert not p.is_found

    p = project.find_program('echo_cmd', ('a_random_name_that_wont_be_matched', 'a_random_name_that_wont_be_matched2'))
    assert p.path is None
    assert p.name == 'echo_cmd'
    assert not p.is_found

  def test_find_programm_notfound_raise(self, project:Project):
    p = project.find_program('echo_cmd', 'a_random_name_that_wont_be_matched')
    assert p.path is None

    with pytest.raises(ProgramNotFoundError) :
      p.exec()
    with pytest.raises(ProgramNotFoundError) :
      p.run()
    with pytest.raises(ProgramNotFoundError) :
      p.Popen()
    with pytest.raises(ProgramNotFoundError) :
      p.rule()

  def test_exec_simple(self, mock_subprocess, prog):
    m_run, m_popen, r_run, r_popen = mock_subprocess
    
    r = prog.exec()
    m_run.assert_called_with(['echo'], stdin=None, capture=True)
    assert r == (r_run.returncode, r_run.stdout, r_run.stderr)
    
    r = prog.exec(other_kw=12345)
    m_run.assert_called_with(['echo'], stdin=None, capture=True, other_kw=12345)
    assert r == (r_run.returncode, r_run.stdout, r_run.stderr)
    
    r = prog.exec('test')
    m_run.assert_called_with(['echo', 'test'], stdin=None, capture=True)
    assert r == (r_run.returncode, r_run.stdout, r_run.stderr)

    r = prog.exec(('test',))
    m_run.assert_called_with(['echo', 'test'], stdin=None, capture=True)
    assert r == (r_run.returncode, r_run.stdout, r_run.stderr)
    
    r = prog.exec(('test1','test2 etc'))
    m_run.assert_called_with(['echo', 'test1', 'test2 etc'], stdin=None, capture=True)
    assert r == (r_run.returncode, r_run.stdout, r_run.stderr)
    
    r = prog.exec('test1','test2 etc')
    m_run.assert_called_with(['echo', 'test1', 'test2 etc'], stdin=None, capture=True)
    assert r == (r_run.returncode, r_run.stdout, r_run.stderr)
    
  def test_exec_input(self, mock_subprocess, prog):
    m_run, m_popen, r_run, r_popen = mock_subprocess
    r = prog.exec(input='TEST')
    m_run.assert_called_with(['echo'], text=True, input='TEST', capture=True)
    assert r == (r_run.returncode, r_run.stdout, r_run.stderr)
    
    r = prog.exec(input=b'TEST')
    m_run.assert_called_with(['echo'], text=False, input=b'TEST', capture=True)
    assert r == (r_run.returncode, r_run.stdout, r_run.stderr)
    
    r = prog.exec(input='TEST', text=True)
    m_run.assert_called_with(['echo'], text=True, input='TEST', capture=True)
    assert r == (r_run.returncode, r_run.stdout, r_run.stderr)
    
    r = prog.exec(input=b'TEST', text=False)
    m_run.assert_called_with(['echo'], text=False, input=b'TEST', capture=True)
    assert r == (r_run.returncode, r_run.stdout, r_run.stderr)
    
    r = prog.exec(input=b'TEST', text=True)
    m_run.assert_called_with(['echo'], text=True, input='TEST', capture=True)
    assert r == (r_run.returncode, r_run.stdout, r_run.stderr)
    
    r = prog.exec(input='TEST', text=False)
    m_run.assert_called_with(['echo'], text=False, input=b'TEST', capture=True)
    assert r == (r_run.returncode, r_run.stdout, r_run.stderr)
    
    input = StringIO('TEST')
    r = prog.exec(input=input)
    m_run.assert_called_with(['echo'], stdin=input, capture=True)
    assert r == (r_run.returncode, r_run.stdout, r_run.stderr)

  def test_run(self, mock_subprocess, prog):
    m_run, m_popen, r_run, r_popen = mock_subprocess
    
    r = prog.run()
    m_run.assert_called_with(['echo'])
    assert r is r_run
    
    r = prog.run('test')
    m_run.assert_called_with(['echo', 'test'])
    assert r is r_run
    
    r = prog.run(('test1', 'test2'))
    m_run.assert_called_with(['echo', 'test1', 'test2'])
    assert r is r_run
    
    r = prog.run('test1', 'test2')
    m_run.assert_called_with(['echo', 'test1', 'test2'])
    assert r is r_run
    
    r = prog.run(('test1', 'test2'), kw=42)
    m_run.assert_called_with(['echo', 'test1', 'test2'], kw=42)
    assert r is r_run
    
    r = prog.run('test1', 'test2', kw=42)
    m_run.assert_called_with(['echo', 'test1', 'test2'], kw=42)
    assert r is r_run
    
    
  def test_popen(self, mock_subprocess, prog):
    m_run, m_popen, r_run, r_popen = mock_subprocess
    
    r = prog.Popen()
    m_popen.assert_called_with(['echo'])
    assert r is r_popen
    
    r = prog.Popen('test')
    m_popen.assert_called_with(['echo', 'test'])
    assert r is r_popen
    
    r = prog.Popen(('test1', 'test2'))
    m_popen.assert_called_with(['echo', 'test1', 'test2'])
    assert r is r_popen
    
    r = prog.Popen('test1', 'test2')
    m_popen.assert_called_with(['echo', 'test1', 'test2'])
    assert r is r_popen
    
    r = prog.Popen(('test1', 'test2'), kw=42)
    m_popen.assert_called_with(['echo', 'test1', 'test2'], kw=42)
    assert r is r_popen
    
    r = prog.Popen('test1', 'test2', kw=42)
    m_popen.assert_called_with(['echo', 'test1', 'test2'], kw=42)
    assert r is r_popen

  def test_rule(self, mock_subprocess, prog):
    m_rule, m_popen, r_rule, r_popen = mock_subprocess
    
    r = prog.rule()
    assert 'echo' == str(r.command.value)
    assert 'echo_cmd' == r.name
    
    r = prog.rule('test', name='echo1')
    assert 'echo$ test' == str(r.command.value)
    assert 'echo1' == r.name
    
    r = prog.rule(('test1', 'test2 etc'), name='echo2')
    assert "echo$ test1$ 'test2$ etc'" == str(r.command.value)
    assert 'echo2' == r.name
    
    r = prog.rule('test1', 'test2 etc', name='echo3')
    assert "echo$ test1$ 'test2$ etc'" == str(r.command.value)
    assert 'echo3' == r.name
    
    r = prog.rule(('test1', 'test2 etc'), kw='42', name='echo4')
    assert "echo$ test1$ 'test2$ etc'" == str(r.command.value)
    assert '42' == str(r.kw.value)
    assert 'echo4' == r.name
    
    r = prog.rule('test1', 'test2 etc', kw='42', name='echo5')
    assert "echo$ test1$ 'test2$ etc'" == str(r.command.value)
    assert '42' == str(r.kw.value)
    assert 'echo5' == r.name
    
    r = prog.rule('test1', 'test2 etc', kw='42', name="echo6")
    assert "echo$ test1$ 'test2$ etc'" == str(r.command.value)
    assert '42' == str(r.kw.value)
    assert 'echo6' == r.name

    
