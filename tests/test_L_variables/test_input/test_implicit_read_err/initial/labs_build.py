from labs import *
from labs import VariableTypeError
import pytest

with pytest.raises(VariableTypeError) as exc_info :
  build.IN_INT = LVariable.I(42, doc="Int variable")
assert exc_info.match('IN_INT')
assert exc_info.match('NUMBER')
assert exc_info.match('"str_value"')
  
with pytest.raises(VariableTypeError) as exc_info :
  build.IN_BOOL = LVariable.I(True, "Bool variable")
assert exc_info.match('IN_BOOL')
assert exc_info.match('BOOL')
assert exc_info.match('"str_value2"')

