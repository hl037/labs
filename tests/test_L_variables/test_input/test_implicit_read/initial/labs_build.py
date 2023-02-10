from labs import *

build.IN_STRING = LVariable.I("Test", doc="String variable")
assert build.IN_STRING.value == "Test2"
assert isinstance(build.IN_STRING.value, str)

build.IN_INT = LVariable.I(42, doc="Int variable")
assert build.IN_INT.value == 43.0
assert isinstance(build.IN_INT.value, float)

build.IN_FLOAT = LVariable.I(42.5, doc="Float variable")
assert build.IN_FLOAT.value == 43.5
assert isinstance(build.IN_FLOAT.value, float)

build.IN_PATH = LVariable.I(Path('test1/test2'), doc="Path variable")
assert build.IN_PATH.value == Path('test1/test2')
assert isinstance(build.IN_PATH.value, Path)

build.IN_FILEPATH = LVariable.I(Path('test2/test3'), doc="Filepath variable")
assert build.IN_FILEPATH.value == Path('test2/test4')
assert isinstance(build.IN_FILEPATH.value, Path)

build.IN_BOOL = LVariable.I(True, "Bool variable")
assert build.IN_BOOL.value == False
assert isinstance(build.IN_BOOL.value, Path)

