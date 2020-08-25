# L.A.B.S

L.A.B.S. stands for Language Agnostic Build System.

This is "yet another" build system to replace cmake and meson.

Labs is not meant to be "the faster" (even though its use of ninja similar to meson makes roughly as fast as meson), but to produce reproductible builds.

Contrary to CMake or Meson, you don't need to learn yet another language since plain python is used.

The philosophy behind Labs is that simple tasks should be trivial to do, and hard ones should be easy.

# A work in progress

The project is still at a draft step : Only the low-level api is developped yet, but it is on heavy developpment, thus expect additionnal feature coming fast.

# Roadmap

  - [x] Ninja abstraction and build generation
    - [x] Variables
    - [x] Rule with variables
    - [x] Target files set
    - [x] Build rules
      - [x] Explicit, implicit and order-only targets
      - [x] Overide variables
  - [x] CMake-like build configuration
  - [x] Basic find\_program
    - [x] Find program in path
    - [x] Find program from several names
  - [x] Easy for a build to depend on a found program
  - [x] Run found program at config time
  - [x] Run found programm at ninja
  - [x] Custom commands (with pipes, file redirection etc.)
  - [x] Command line interface
    - [x] CMake-like semantic shadow build
    - [x] CMake-like incremental cache
  - [x] Feature testing framework
  - [ ] Documentation
    - [x] In code docstring
    - [ ] Tutorial
  - [ ] Extension system
  - [ ] Install rules
  - [ ] GCC compatible workflow (anything that compiles to \*.o files
    - [ ] Compile wrapper class
    - [ ] Understand common C/CXX env variables
    - [ ] Handle include paths
    - [ ] Handle libs
  - [ ] auto\_build function to compile with the right compiler automatically regarding the file ype.
  - [ ] sub project
  - [ ] find\_lib
    - [ ] using pkg_config
    - [ ] using CMake
  - [ ] Java compilation
  - [ ] Qt
  - [ ] Other language
    - [ ] Go
    - [ ] Rust
    - [ ] ...
  - [ ] Wrapper to handle linux and windows with the same commands
  - [ ] Build an execurable for windows embedding the python interpreter
  - [ ] IDE project generation
  - [ ] Advanced find\_program
    - [ ] Require version
    - [ ] Host, build and target machin distinction
    - [ ] Look at python modules
  - [ ] support a wide range of compilers

  Don't be fooled : half of the features are checked, but it actually represent at most 5% of the targeted features =))

  If you like the project, feel free to apply for implement some feature by creating an issue !

# License

Copyright © 2020 Léo Flaventin Hauchecorne

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.


