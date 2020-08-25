
concat = Rule('concat', command='cat '+v_in+' > '+v_out) << find_program('cat')

(src/'truc1', src/'machin1') >> concat.build() >> (build/'truc2')


