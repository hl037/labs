import os
import pytest
import filecmp
import pytest_datadir_ng
from labs import Labs
from pathlib import Path
from unittest.mock import Mock

def assertDirsEqual(d1, d2):
  cmp = filecmp.dircmp(d1, d2)
  assert cmp.right_only == []
  assert cmp.left_only == []
  assert cmp.diff_files == []

def assertFilesEqual(f1, f2):
  assert filecmp.cmp(f1, f2, shallow=False)
  
  
@pytest.fixture
def mock_shutil(monkeypatch):
  mock_which = Mock(side_effect=lambda x:f'/bin/{x}')
  monkeypatch.setattr('shutil.which', mock_which)
  
@pytest.fixture
def check_labs(datadir_copy, datadir):
  t = Path(datadir_copy['t'])
  r = Path(datadir['r'])
  config_src = Path(datadir['config']).read_text()
  config = eval(config_src, globals(), locals())
  config[Labs.absolute_path_key] = '0'
  config[Labs.relative_path_key] = '1'
  _r = t.parent/'_r'
  _r.mkdir(parents=True, exist_ok=True)
  def check(use_cache=False):
    l = Labs(t, _r, config, use_cache)
    l.process()
    assertDirsEqual(r, _r)
  os.chdir(_r)
  return check

def test_empty(check_labs, mock_shutil):
  check_labs()

def test_simple(check_labs, mock_shutil):
  check_labs()

def test_ext(check_labs, mock_shutil):
  check_labs()
  
def test_install(check_labs, mock_shutil):
  check_labs()
