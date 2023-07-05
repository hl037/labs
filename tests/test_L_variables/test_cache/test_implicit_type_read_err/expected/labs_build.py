from labs import *
import pytest

with pytest.raises(ValueError) as exc_info :
  build.IN_INT = lvariable(42, doc="Int variable")
assert exc_info.match('IN_INT')
assert exc_info.match('INT')
assert exc_info.match('"str_value"')
  
with pytest.raises(ValueError) as exc_info :
  build.IN_BOOL = lvariable(True, doc="Bool variable")
assert exc_info.match('IN_BOOL')
assert exc_info.match('BOOL')
assert exc_info.match('"str_value2"')

