from pathlib import Path
import pytest
from labs import (
  CVariable,
  LVariable,
  BVariable,
  LBVariable,
  BRVariable,
  brvariable,
  BRule,
  BStep,
  STRING,
  INT,
  FLOAT,
  PATH,
  FILEPATH,
  BOOL,
  Expr,
  CacheValueError,
  VariableReferenceCycleError,
  ExprTypeError,
)

def test_default_value_init():
  var = LVariable(Expr("Test"), STRING, "", None, "var")
  value = var.value
  assert isinstance(value, str)
  assert value == "Test"
  
  var = LVariable(Expr("42"), INT, "", None, "var")
  value = var.value
  assert isinstance(value, int)
  assert value == 42
  
  var = LVariable(Expr("42.5"), FLOAT, "", None, "var")
  value = var.value
  assert isinstance(value, float)
  assert value == 42.5
  
  var = LVariable(Expr("on"), BOOL, "", None, "var")
  value = var.value
  assert isinstance(value, bool)
  assert value == True
  
  var = LVariable(Expr("foo/bar"), PATH, "", None, "var")
  value = var.value
  assert isinstance(value, Path)
  assert value == Path("foo/bar")
  
  var = LVariable(Expr("foo/bar"), FILEPATH, "", None, "var")
  value = var.value
  assert isinstance(value, Path)
  assert value == Path("foo/bar")
  
def test_double_access_value():
  var = LVariable(Expr("Test"), STRING, "", None, "var")
  value = var.value
  value2 = var.value
  assert value == "Test"
  assert value2 == "Test"
  
  var = LVariable(Expr("42"), INT, "", None, "var")
  value = var.value
  value2 = var.value
  assert value == 42
  assert value2 == 42
  
  var = LVariable(Expr("42.5"), FLOAT, "", None, "var")
  value = var.value
  value2 = var.value
  assert value == 42.5
  assert value2 == 42.5
  
  var = LVariable(Expr("on"), BOOL, "", None, "var")
  value = var.value
  value2 = var.value
  assert value == True
  assert value2 == True
  
  var = LVariable(Expr("foo/bar"), PATH, "", None, "var")
  value = var.value
  value2 = var.value
  assert value == Path("foo/bar")
  assert value2 == Path("foo/bar")
  
  var = LVariable(Expr("foo/bar"), FILEPATH, "", None, "var")
  value = var.value
  value2 = var.value
  assert value == Path("foo/bar")
  assert value2 == Path("foo/bar")


def test_concat():
  var = LVariable(Expr("4")+Expr("2"), INT, "", None, "var")
  value = var.value
  value2 = var.value
  assert value == 42
  assert value2 == 42
  
  var = LVariable(Expr("4")+"2", INT, "", None, "var")
  value = var.value
  value2 = var.value
  assert value == 42
  assert value2 == 42
  
  var = LVariable("4"+Expr("2"), INT, "", None, "var")
  value = var.value
  value2 = var.value
  assert value == 42
  assert value2 == 42
  
  var = LVariable(Expr(f'{Expr("4")}{Expr("2")}'), INT, "", None, "var")
  value = var.value
  value2 = var.value
  assert value == 42
  assert value2 == 42


def test_variable_resolution_nocache(expectBuild):
  expectBuild()
  
def test_variable_resolution_cache(expectBuild):
  expectBuild()
  
def test_variable_err_does_not_exist(expectBuild):
  with pytest.raises(CacheValueError) as exc_info:
    expectBuild()
  assert exc_info.match('assign var3')
  assert exc_info.match('`does_not_exist` does not exist')


def test_cycle_detection_cvar(expectBuild):
  with pytest.raises(CacheValueError) as exc_info:
    expectBuild()
  assert exc_info.match('assign var3 from cache')
  assert exc_info.match('var3->var1->var2->var3')
  
def test_cycle_detection_bvar():
  with pytest.raises(VariableReferenceCycleError) as exc_info:
    var1 = BVariable("", None, "var1")
    var2 = BVariable("", None, "var2")
    var3 = BVariable("", None, "var3")
    var1.expr = var2
    var2.expr = var3
    var3.expr = var1
  assert exc_info.match('assigning var3')
  assert exc_info.match('var3->var1->var2->var3')

def test_assign_bvar_to_lvar_err():
  bvar = BVariable('', None, 'bvar')
  bvar.expr = "test"
  lvar = LVariable(f'This is a Test with {bvar} assigned to lvar', STRING, "", None, "lvar")
  with pytest.raises(ExprTypeError) as exc_info:
    lvar.evaluate()
  assert exc_info.match('bvar')
  assert exc_info.match('lvar')
  assert exc_info.match(r'assigned to LVariable\(')

@pytest.mark.skip(reason="Need to refacto to decouple ninja")
def test_bvar_build_expr():
  lvar1 = LVariable('This', STRING, "", None, "lvar1")
  lvar2 = LVariable(f'{lvar1} is', STRING, "", None, "lvar2")
  cvar1 = CVariable(None, 'cvar1', 'test', '')
  cvar2 = CVariable(None, 'cvar2', f'a {cvar1}', '')
  bvar1 = BVariable('', None, 'bvar1', 'Dummy value')
  bvar2 = BVariable('', None, 'bvar2', f'Here, {lvar2} {cvar2}. {bvar1}')

  assert bvar2.build_expr == 'Here, This is a test. $(bvar1)'
  assert bvar2.expanded == 'Here, This is a test. Dummy value'

@pytest.mark.skip(reason="Need to refacto to decouple ninja")
def test_lbvar_exprs():
  lvar1 = LVariable('This', STRING, "", None, "lvar1")
  lvar2 = LVariable(f'{lvar1} is', STRING, "", None, "lvar2")
  cvar1 = CVariable(None, 'cvar1', 'test', '')
  cvar2 = CVariable(None, 'cvar2', f'a {cvar1}', '')
  lbvar1 = LBVariable('Dummy value', STRING, '', None, 'lbvar1')
  lbvar2 = LBVariable(f'Here, {lvar2} {cvar2}. {lbvar1}', STRING, '', None, 'lbvar2')

  assert lbvar2.build_expr == 'Here, This is a test. $(lbvar1)'
  assert lbvar2.cache_expr == 'Here, $(lvar2) $(cvar2). $(lbvar1)'
  assert lbvar2.expanded == 'Here, This is a test. Dummy value'

@pytest.mark.skip(reason="Need to refacto to decouple ninja")
def test_brvar_exprs():
  lvar1 = LVariable('This', STRING, "", None, "lvar1")
  lvar2 = LVariable(f'{lvar1} is', STRING, "", None, "lvar2")
  cvar1 = CVariable(None, 'cvar1', 'test', '')
  cvar2 = CVariable(None, 'cvar2', f'a {cvar1}', '')
  lbvar1 = LBVariable('Dummy value', STRING, '', None, 'lbvar1')
  lbvar2 = LBVariable(f'Here, {lvar2} {cvar2}. {lbvar1}', STRING, '', None, 'lbvar2')
  r = BRule(None, 'Test rule')
  r.brv1 = brvariable(lbvar2)
  r.brv2 = f'Here, {lvar2} {cvar2}. {lbvar1}. Again {r.brv1}'

  assert lbvar2.build_expr == 'Here, This is a test. $(lbvar1)'
  assert lbvar2.cache_expr == 'Here, $(lvar2) $(cvar2). $(lbvar1)'
  assert lbvar2.expanded == 'Here, This is a test. Dummy value'
  

# 
# #TODO: test BVariable
# 
#   
# def test_(expectBuild):
#   expectBuild()
#   
