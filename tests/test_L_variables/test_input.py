

def test_err_redeclare(expectdir, build):
  with expectdir() as e :
      build(e)

def test_implicit_type_decl(expectdir, build):
  with expectdir() as e :
    build(e)

def test_explicit_type_decl(expectdir, build):
  with expectdir() as e :
    build(e)
  
def test_implicit_type_read(expectdir, build):
  with expectdir() as e :
    build(e)

def test_explicit_type_read(expectdir, build):
  with expectdir() as e :
    build(e)

def test_implicit_type_read_err(expectdir, build):
  with expectdir() as e :
    build(e)

def test_explicit_type_read_err(expectdir, build):
  with expectdir() as e :
    build(e)



