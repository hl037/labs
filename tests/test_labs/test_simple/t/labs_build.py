
concat = Rule('concat', command='cat '+v_in+' > '+v_out) << find_program('cat')

(src_dir/'truc1', src_dir/'machin1') >> concat.build() >> (build_dir/'truc2')


