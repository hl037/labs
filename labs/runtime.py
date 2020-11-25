import typing

if typing.TYPE_CHECKING :
  import labs

_ctx = None

def get_ctx() -> "labs.LabsContext":
  return _ctx

