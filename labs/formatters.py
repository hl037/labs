from .core import formatter
from .variables import Expandable, Referenceable, CacheOutput, LBVariable

@formatter('expanded', 'e')
def format_expanded(self):
  if isinstance(self, Expandable) :
    return self.expanded
  raise TypeError()

@formatter('cache_reference', 'cr')
def format_cache_reference(self):
  if isinstance(self, CacheOutput) :
    return f'$({self.name})'
  raise TypeError()

@formatter('reference', 'r', 'ref', '')
def format_reference(self):
  if isinstance(self, Referenceable) :
    return f'$(\x00{id(self)})'
  raise TypeError()
  
