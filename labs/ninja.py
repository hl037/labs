from .core import Formatter
from .variables import Expandable
from .metabuild import GBVariable, BRVariable, BuiltinBRVariable, BRule, BStep

def scoped_name(var:BVariable):
  if isinstance(var, BRVariable) :
    if isinstance(self, BuiltinBRVariable) :
      return var.name
    return f'_rule_{var.rule._internal.name}_{var.name})'
  return var.name
    

format_ninja_reference = Formatter('ninja_reference', 'nr')

@format_ninja_reference.sub(BVariable)
def _(self:Bvariable):
  return f'$({scoped_name(self)})'

@format_ninja_reference.sub(Expandable)
def _(self:Expandable):
  return self.expanded
  

def bvariable_adj_cb(var:GBVariable):
  expr = var.expr
  return ( p for p in expr.parts if isinstance(p, GBVariable) )


format_ninja = Formatter('ninja', 'n')

@format_ninja.sub(GBVariable)
def _(self:GBVariable):
  return f'{scoped_name(self)} = {format(self.expr, "nr")}'
  
@format_ninja.sub(BRule)
def _(self:BRule):
  variables = sorted(self._internal.builtins.values(), lambda v: v.name)
  variable_txt = ''.join( f'\n  {var:n}' for var in variables )
  return f'rule {self._internal.name}:{variable_txt}'
