
alt_v_in = Variable('alternative_input', f'{src/"truc1"} {src/"machin1"}')

concat = Rule('concat', command='cat '+v_in+' '+alt_v_in+' > '+v_out) << find_program('cat')

implicit(src/'truc1', src/'machin1') >> concat.build() >> (build/'truc2')


