#!/bin/zsh
for d in ./test_* ; do mkdir -p $d/expected/build; pushd $d/expected; echo "\n\n"$d"\n\n"; cp -r ../initial/* .; pushd build; sed -e "s#{{test_dir}}#`realpath ../../initial`#" -i labs_cache build.ninja ; labs ../../initial ; sed -e "s#`realpath ../../initial`#{{test_dir}}#" -i labs_cache build.ninja; popd; popd; done
