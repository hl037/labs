from labs import *
import pytest

build.IN_STRING = lvariable("Test", STRING, doc="String variable")

with pytest.raises(BuildObjectRedeclaredError) as exc_info :
  build.IN_STRING = lvariable("Test", STRING, doc="String variable")
assert exc_info.match('LVariable')
assert exc_info.match('IN_STRING')

