

from labs import Labs
from addict import Dict as C
import click


@click.command(name="labs")
@click.argument('src', nargs=1, required=False, default=None)
@click.option('--build-dir', '-C', type=str, default=None)
@click.option('-D', type=str, multiple=True)
@click.option('--debug', '-g', is_flag=True, default=False)
@click.option('--clean', is_flag=True)
def main(src, build_dir, d, debug, clean):
  try:
    D = d
    config = dict(d.split('=', maxsplit=1) for d in D)
    labs = Labs(src, build_dir, config, use_cache=not clean)
    labs.process()
  except:
    if debug :
      import pdb; pdb.xpm()
    else:
      raise

if __name__ == "__main__" :
  main()



