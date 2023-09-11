from .core import formatter
from .variables import BVariable
from .metabuild import BRVariable, BuiltinBRVariable, BRule, BStep

def scoped_name(var:BVariable):
  if isinstance(var, BRVariable) :
    if isinstance(self, BuiltinBRVariable) :
      return var.name
    return f'_rule_{var.rule._internal.name}_{var.name})'
  return var.name
    

@formatter('ninja_reference', 'nr')
def format_ninja_reference(self):
  if isinstance(self, BVariable) :
    return f'$({scoped_name(self)})'
    
  if isinstance(self, Expandable) :
    return self.expanded
  raise TypeError()

def bvariable_adj_cb(var:BVariable):
  expr = var.expr


@formatter('ninja', 'n')
def format_ninja(self):
  if isinstance(self, BVariable) :
    return f'{scoped_name(self)} = {format(self.expr, "nr")}'
  if isinstance(self, BRule) :
    variables = 
    
  if isinstance(self, Expandable) :
    return self.expanded
  raise TypeError()

