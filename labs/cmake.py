from __future__ import annotations

import re
from pathlib import Path
from typing import TYPE_CHECKING
  
from .utils import Dict
from .variables import LVariable, Expr

if TYPE_CHECKING :
  from typing import IO

_id = r'[_a-zA-Z][_0-9A-Za-z]*'
cache_variable_re = re.compile(rf'(?P<key>{_id}):(?P<type>{_id})=(?P<value>.*)$')
deescape_re = r'(?<dollar>\\$)|\$\((?P<var>{id})\)'
doc_re = re.compile(r'// (?P<doc>.*)')
del _id


def escape(s:str):
  return s.replace('$', '\\$')

def deescape_sub(m:re.Match):
  if m['dollar'] :
    return '$'
  if m['var'] :
    return f'$(\x00{m["var"]})'

def deescape(s:str):
  return


def parse_cache(line_iterator):
  opts = {}
  raw_doc = []
  for l in line_iterator :
    if m := doc_re.match(l) :
      raw_doc.append(m['doc'])
    elif m := cache_variable_re.match(l) :
      opts[m['key']] = m['value'], raw_doc
      raw_doc = []
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
    res += '// '
    if desc :
      res += desc + ' '
    if default_value is not None :
      res += f'(Default : {default_value})'
    res += '\n'
  res += f'{name}:{type}={value}'
  return res

def writeCache(f:IO, variables: dict[str, LVariable]):
  variable_list = list(variables.values())
  for v in variable_list:
    if not v.isEvaluated :
      v.evaluate()
  variable_list.sort(key=lambda v: v.name)
  for v in variable_list :
    f.write(varToCache(
      v.name,
      v.cache_expr,
      v.type.__name__,
      v.doc,
      format(v.default_value, 'c') if isinstance(v.default_value, Expr) else v.type.dumps(v.default_value)
    ))
    f.write('\n\n')
