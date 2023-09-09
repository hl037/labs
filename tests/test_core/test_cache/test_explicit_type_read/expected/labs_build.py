from labs import *

build.IN_STRING = lvariable("Test", STRING, doc="String variable")
assert build.IN_STRING.value == "Test2"
assert isinstance(build.IN_STRING.value, str)

build.IN_INT = lvariable(42, INT, doc="Int variable")
assert build.IN_INT.value == 43
assert isinstance(build.IN_INT.value, int)

build.IN_FLOAT = lvariable(42.5, FLOAT, doc="Float variable")
assert build.IN_FLOAT.value == 43.5
assert isinstance(build.IN_FLOAT.value, float)

build.IN_PATH = lvariable(Path('test1/test2'), PATH, doc="Path variable")
assert build.IN_PATH.value == Path('test1/test3')
assert isinstance(build.IN_PATH.value, Path)

build.IN_FILEPATH = lvariable(Path('test2/test3'), FILEPATH, doc="Filepath variable")
assert build.IN_FILEPATH.value == Path('test2/test4')
assert isinstance(build.IN_FILEPATH.value, Path)

build.IN_BOOL = lvariable(True, BOOL, "Bool variable")
assert build.IN_BOOL.value == False
assert isinstance(build.IN_BOOL.value, bool)

