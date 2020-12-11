from labs.ext.install import Install

install = Install(dest='../rt')

install.add_data('t1', sub_path='TEST')

install.add_files(glob('**/t*'), dest='ROOT', sub_path='res/gather')

install.replicate(glob('**/t*'), base_dir=src_dir, dest='ROOT', sub_path='res/replicate')

install.mkdir('mk/dir1/dir2', 'mk/dir3', 'mk/dir4', 'mk/dir4/dir5', dest='ROOT')

install.add_dir_rec('rec', dest='ROOT', sub_path='res/rec', user='root', group='root', mode=0o777)





