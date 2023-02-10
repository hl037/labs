

def test_explicit(expectdir, build):
  with expectdir() as e :
    build(e)
    
def test_implicit(expectdir, build):
  with expectdir() as e :
    build(e)

def test_err_redeclare(expectdir, build):
  with expectdir() as e :
      build(e)

def test_implicit_read(expectdir, build):
  with expectdir() as e :
    build(e)

def test_explicit_read(expectdir, build):
  with expectdir() as e :
    build(e)
  
def test_implicit_read_err(expectdir, build):
  with expectdir() as e :
    build(e)

def test_explicit_read_err(expectdir, build):
  with expectdir() as e :
    build(e)

def test_implicit_read_err_type(expectdir, build):
  with expectdir() as e :
    build(e)

def test_explicit_read_err_type(expectdir, build):
  with expectdir() as e :
    build(e)



