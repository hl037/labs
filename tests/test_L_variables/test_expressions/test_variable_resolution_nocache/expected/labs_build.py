from labs import *
import pytest


build.var1 = lvariable("4", STRING, "var 1")

build.var2 = lvariable("2", STRING, "var 2")

build.var3 = lvariable(build.var1 + build.var2, INT, "var1 + var2")

assert build.var3.value == 42

