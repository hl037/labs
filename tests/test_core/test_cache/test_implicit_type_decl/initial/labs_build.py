from labs import *

build.IN_STRING = lvariable("Test", doc="String variable")
build.IN_INT = lvariable(42, doc="Int variable")
build.IN_FLOAT = lvariable(42.5, doc="Float variable")
build.IN_PATH = lvariable(Path('test1/test2'), doc="Path variable")
build.IN_FILEPATH = lvariable(Path('test2/test3'), doc="Filepath variable")
build.IN_BOOL = lvariable(True, doc="Bool variable")
