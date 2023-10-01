from .core import Formatter
from . import variables

Expandable = variables.Expandable
Referenceable = variables.Referenceable
CacheOutput = variables.CacheOutput



format_expanded = Formatter('expanded', 'e')

@format_expanded.sub(Expandable)
def _(self:Expandable):
  return self.expanded


format_cache_reference = Formatter('cache_reference', 'cr')

@format_cache_reference.sub(CacheOutput)
def _(self:CacheOutput):
  return f'$({self.name})'


format_reference = Formatter('reference', 'r', 'ref', '')

@format_reference.sub(Referenceable)
def _(self:Referenceable):
  return f'$(\x00{id(self)})'
  
  
