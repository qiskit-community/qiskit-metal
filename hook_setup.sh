#!/bin/bash

ln -s -f ../../hooks/pre-commit .git/hooks/pre-commit
ret=$?
if [[ $ret == 0 ]]; then
    echo "Linking hooks succeeded!"
else
    echo "Linking hooks failed with rc $ret"
fi
