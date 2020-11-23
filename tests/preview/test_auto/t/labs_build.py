b = auto.build('test.c', 'test.cpp', name='testlib', type=('static', 'lib')) << auto.flag.PIE << auto.flags('PIC', 'c++17')



#


c = auto.compiler('c', name=None, target_arch=None, build_arch=None, )

c << auto.flags('PIC', 'c++17')









