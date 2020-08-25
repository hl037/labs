import re

_id = r'[_a-zA-Z][_0-9A-Za-z]*'
cache_variable_re = re.compile(rf'(?P<key>{_id}):(?P<type>{_id})=(?P<value>.*)$')
del _id

def parse_cache(line_iterator):
  opts = {}
  for l in line_iterator :
    m = cache_variable_re.match(l)
    if m :
      opts[m['key']] = m['value']
  return opts
    

def str2bool(s:str) -> bool:
  if isinstance(s, bool) :
    return s
  cmp = s.lower()
  if cmp in ('false', 'no', 'n', 'off', '0') :
    return False
  if cmp in ('true', 'yes', 'y', 'on', '1') :
    return True
  raise ValueError(s)

def varToCache(name:str, value:str, type:str='INTERNAL', desc:str=None, default_value:str=None):
  res = ''
  if desc or default_value:
    res += '//'
    if desc :
      res += desc + ' '
    if default_value :
      res += f'(Default : {default_value}'
    res += '\n'
  res += f'{name}:{type}={value}'
  return res
  

