from labs import *

build.IN_STRING = LVariable.I("Test", doc="String variable")
build.IN_INT = LVariable.I(42, doc="Int variable")
build.IN_FLOAT = LVariable.I(42.5, doc="Float variable")
build.IN_PATH = LVariable.I(Path('test1/test2'), doc="Path variable")
build.IN_FILEPATH = LVariable.I(Path('test2/test3'), doc="Filepath variable")
build.IN_BOOL = LVariable.I(True, doc="Bool variable")
