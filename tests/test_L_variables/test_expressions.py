from pathlib import Path
import pytest
from labs import LVariable, STRING, INT, FLOAT, PATH, FILEPATH, BOOL, Expr, CacheValueError

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
  
# 
# #TODO: test BVariable
# 
#   
# def test_(expectBuild):
#   expectBuild()
#   
