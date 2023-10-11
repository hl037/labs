
from labs import *

build.ZTEST_VAR = bvariable('Test')
build.XTEST_VAR2 = bvariable(build.ZTEST_VAR + 'Test 2')
build.ATEST_VAR3 = bvariable(build.XTEST_VAR2 + build.XTEST_VAR2)

r = build.add_brule("my_rule")
r.test_rvariable = "This is a test"
r.command = r.test_rvariable + ' then ' + build.ATEST_VAR3


