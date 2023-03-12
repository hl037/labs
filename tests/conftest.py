import pytest
from labs.cli import main
from pprint import pprint

@pytest.fixture
def build():
  def build(directory, *args):
    print('TTT 1')
    try :
      main([str(directory), '-C', str(directory / 'build'), *args])
    except SystemExit:
      pass
    print('TTT 2')
  return build
  
