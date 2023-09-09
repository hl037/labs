from labs import *

build.IN_STRING = lvariable("Test", STRING, doc="String variable")
build.IN_INT = lvariable(42, INT, doc="Int variable")
build.IN_FLOAT = lvariable(42.5, FLOAT, doc="Float variable")
build.IN_NUMBER = lvariable(42.5, NUMBER, doc="Float variable")
build.IN_PATH = lvariable(Path('test1/test2'), PATH, doc="Path variable")
build.IN_FILEPATH = lvariable(Path('test2/test3'), FILEPATH, doc="Filepath variable")
build.IN_BOOL = lvariable(True, BOOL, "Bool variable")

