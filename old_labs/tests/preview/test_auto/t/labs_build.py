
# 




from labs.ext.esp8266 import NodeMCUv3 as TC

tc = TC()

lib = tc.build("lib/truc/*", 
tc.build(glob("src/*"))
tc.






# old
from functools import cached_property


b = auto.build('test.c', 'test.cpp', name='testlib', type=('static', 'lib')) << auto.flag.PIE << auto.flags('PIC', 'c++17')



#


c = auto.compiler('c', name=None, target_arch=None, build_arch=None, )

c << auto.flags('PIC', 'c++17')

#

from labs.ext.gcc import GCC
from labs.ext.install import Install

install = Install()
gcc = GCC()
lib = gcc.library("mylib", glob("src/*.c"))
install.add(lib)

#

from labs.ext.gcc import GCC
from labs.ext.install import Install

install = Install()
gcc = GCC()
opencv = gcc.findLibrary("opencv")
opencv = gcc.findLibrary("opencv", link="static")
opencv = gcc.findLibrary("opencv", link="shared")
lib = gcc.shared_library("mylib", glob("src/*.c"), opencv)
lib = gcc.static_ibrary("mylib", glob("src/*.c"), opencv, link = "static")
install.add(lib)

## Alias
gcc.shared_library(**kwargs) <==> gcc.build(*args, **kwargs, link="shared")
gcc.static_library(**kwargs) <==> gcc.build(*args, **kwargs, link="static")
gcc.executable(*args, **kwargs) <==> gcc.build(*args, **kwargs)


class Build(Node):
  """
  Class permettant de représenter un build (la sortie d'un linker), en gérant l'ajout de à peu près n'importe quel type de fichier à condition qu'un compilateur existe pour celui-ci.
  """
  conf : Dict # Configuration générale pour le build (pareil que pour la Toolchain, mais à un étage en dessous)
  toolchain : "ToolChain"
  compilers : DefaultDict[str, 'Compiler'] # Dict stockant les compilateurs pour chaque type de fichier. Default dict car il fait appel à la toolchain si le compilateur pour le langage n'a pas encore été créé. (toolchain.new_compiler(lang))
  linkers : DefaultDict[str, 'Linker'] # Dict stockant les linkers pour chaque cible du build. Tous les objets du build sont systématiquement passés à tous les linkers. Ce dict peut être vide si link="object_files"
    

class ToolChain(object):
  """
  Boite à outil qui fait office de factory pour les Build. Les méthodes new_compiler et new_linker devraient être les seules à surcharger) 
  """
  conf : Dict # Configuration globale de la toolchain. Possède notamment les flags de base. On peut rajouter une option pour lire les var d'environnement et les stocker ici. Sa structure est la suivante :
  # {
  #   'all' : conf commune à tous les compilers et tous les linkers
  #   'all_compilers' : conf commune à tous les compilateurs
  #   'all_linkers' : conf commune à tous les linkers
  #   'compilers.lang' : conf globale du compilateur de "lang"
  #   'linkers.name' : conf globale des linkers ayant pour nom "name"
  #   ... : Autres configuration spécifiques à la toolchain
  # }
  #
  # L'agrégation des confs pour le compilateur C se fait ainsi (analogue pour le linker):
  #
  # tc.all | tc.all_compilers | tc.compilers.c | compiler.conf | 
  # fileset.conf.all_toolchains.all | fileset.all_toolchain.all_compilers | fileset.all_toolchain.compilers.c |
  # fileset.conf.toolchains[tc.name].all | fileset.conf.toolchains[tc.name].all_compilers | fileset.conf.toolchains[tc.name].compilers.c
  #
  # La conf possède un champs "raw_flags" (nom non définitif) puor envoyer des flags bas-niveau sous la forme d'une Expr
  def shared_library(self, *args, **kwargs) -> Build:
    return self.build(*args, **kwargs, link="shared")

  def static_library(self, *args, **kwargs) -> Build:
    return self.build(*args, **kwargs, link="static")

  def executable(self, *args, **kwargs) -> Build:
    return self.executable(*args, **kwargs, link="executable")
  
  def object_files(self, *args, **kwargs) -> Build:
    return self.executable(*args, **kwargs, link="object_files")
  
  def build(self, *args, **kwargs) -> Build:
    if "conf" in kwargs :
      conf = Dict(kwargs.pop("conf"))
    else:
      conf = Dict()
    conf |= kwargs
    build = self.new_build(conf)
    build.add(*args)

  def new_compiler(self, conf) -> Compiler:
    raise NotImplementedError()
    #L'implémentation doit si possible utiliser un Generic compileur en ne passant qu'une rule issue d'un find program en respectant la convention du GenericCompiler. (possiblité de surcharge à voir pour l'interprétation des options) 

  def new_linker(self, conf):
    raise NotImplementedError()
    # Même remarque que pour le compilateur

  # Possibilité de gérer les compilateur sous la forme :
  def Compiler_lang(self, conf):
    # exemple
    return CCompiler(gcc_program.rule(...))
  
  # Ou sous la forme d'un dict de classes d'héritage, ou encore directement en tant que classes membres :
  class Compiler_lang(GenericCompiler):
    """
    Sous classe du compiler
    """

  class Linker(GenericLinker):
    """
    Sous classe du linker
    """
    # ↑ J'aime bien celui là

class Compiler(Node):
  """
  S'inspirer de la classe déjà écrite dans ext.gcc.
  Doit prendre en paramètre seulement les types de fichiers supportés
  """
  conf : Dict
    
class Linker(Node):
  """
  Un linker est aussi un node. Une même rule peut néanmoins être partagée par deux linkers.
  """
  conf : Dict
    

    





