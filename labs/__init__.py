from __future__ import annotations

from typing import TYPE_CHECKING

from pathlib import Path

from .utils import Dict, relative_to
from .translation import tr

from .main import Labs, LabsBuild, CacheValueError, BuildObjectRedeclaredError, __getattr__ as main__getattr__

from .variables import (
  STRING,
  NUMBER,
  FLOAT,
  INT,
  BOOL,
  PATH,
  FILEPATH,
  VariableType,
  CVariable,
  LVariable,
  ExprTypeError,
  LVariableDecl,
  Expr,
  LVariableAlreadyEvaluatedError,
  LVariableTypeInferenceError,
  lvariable,
  VariableReferenceCycleError,
)

from .metabuild import (
  BVariable,
  GBVariable,
  GBVariableDecl,
  bvariable,
  LBVariable,
  lbvariable,
  LBVariableDecl,
  BRVariable,
  BRVariableDecl,
  brvariable,
  BuiltinBRVariable,
  BRule,
  brule,
  BStep,
  bstep,
)

__getattr__ = main__getattr__

__all__ = [
  'LVariable',
  'build',
  'ctx',
  'BOOL', 'NUMBER', 'INT', 'FLOAT', 'STRING', 'PATH', 'FILEPATH',
  'Expr',
  'Path',
  'Dict',
  'relative_to',
  'BuildObjectRedeclaredError',
  'LVariableAlreadyEvaluatedError',
  'LVariableTypeInferenceError',
  'lvariable',
  'bvariable',
  'brule',
  'bstep'
]


