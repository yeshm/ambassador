#!/bin/sh

set -ex

env | sort 

# Do we have any non-doc changes?
change_count=$(git diff --name-only "$TRAVIS_COMMIT_RANGE" | grep -v '^docs/' | wc -l)

if [ $change_count -eq 0 ]; then
    echo "No non-doc changes"
    exit 0
fi

# Are we on master?
ONMASTER=

if [ \( "$TRAVIS_BRANCH" = "master" \) -a \( -z "TRAVIS_PULL_REQUEST" \) ]; then
    ONMASTER=yes
fi

# Syntactic sugar really...
onmaster () {
    test -n "$ONMASTER"
}

if onmaster; then
    DOCKER_REGISTRY="datawire"
else
    DOCKER_REGISTRY=-
fi

TYPE=$(python scripts/bumptype.py --verbose)

make new-$TYPE

if onmaster; then
    make tag
else
    echo "not on master; not tagging"
fi