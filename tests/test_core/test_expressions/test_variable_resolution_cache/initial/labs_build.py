from labs import *
import pytest


build.var1 = lvariable("4", STRING, "var 1")

build.var2 = lvariable("2", INT, "var 2")

build.var3 = lvariable(build.var1 + build.var2, INT, "var1 + var2")

build.var4 = lvariable(build.var1 + build.var2 + build.var3, INT, "var1 + var2 + var3")

build.var5 = lvariable(20, INT, "var1 + var2 + var3")


assert build.var3.value == 53

assert build.var4.value == 5353

assert build.var5.value == 5351
