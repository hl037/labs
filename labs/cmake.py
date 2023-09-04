from __future__ import annotations

import re
from pathlib import Path
from typing import TYPE_CHECKING
  
from .utils import Dict
from .variables import LVariable, CVariable, Expr

if TYPE_CHECKING :
  from typing import IO

_id = r'[_a-zA-Z][_0-9A-Za-z]*'
cache_variable_re = re.compile(rf'(?P<key>{_id})(:(?P<type>{_id}))?=(?P<value>.*)$')
deescape_re = re.compile(rf'(?P<dollar>\\$)|\$\((?P<var>{_id})\)')
doc_re = re.compile(r'// (?P<doc>.*)')
del _id


def escape(s:str):
  return s.replace('$', '\\$')


def deescape(s:str, get_variable):
  def deescape_sub(m:re.Match):
    if m['dollar'] :
      return '$'
    if m['var'] :
      return format(get_variable(m['var']), 'r')
  return deescape_re.sub(deescape_sub, s)


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

def var_to_cache(name:str, value:str, type:str='INTERNAL', desc:list[str]=[], default_value:str=None):
  desc = list(desc)
  if default_value is not None :
    desc.append(f'(Default : {default_value})')
  res = ''.join(f'// {line}\n' for line in desc)
  res += f'{name}:{type}={value}'
  return res

def write_cache(f:IO, variables: dict[str, LVariable|CVariable]):
  variable_list = list(variables.values())
  for v in variable_list:
    if isinstance(v, LVariable) and not v.is_evaluated :
      v.evaluate()
  variable_list.sort(key=lambda v: v.name)
  for v in variable_list :
    if isinstance(v, LVariable) :
      f.write(var_to_cache(
        v.name,
        v.cache_expr,
        v.type.__name__,
        v.doc,
        format(v.default_value, 'cr') if isinstance(v.default_value, Expr) else v.type.dumps(v.default_value)
      ))
      f.write('\n\n')
    elif isinstance(v, CVariable) :
      f.write(var_to_cache(
        v.name,
        v.cache_expr,
        'STRING(USER)',
        v.doc,
        None
      ))
      f.write('\n\n')
      
