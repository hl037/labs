
from labs import *

build.ZTEST_VAR = bvariable('Test')
build.XTEST_VAR2 = bvariable(build.ZTEST_VAR + 'Test 2')
build.ATEST_VAR3 = bvariable(build.XTEST_VAR2 + build.XTEST_VAR2)


