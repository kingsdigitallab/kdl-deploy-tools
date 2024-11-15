#!/bin/bash

# Mercurial to Git Repository Converter
#
# Prerequisites:
# - hg-fast-export must be installed (https://repo.or.cz/fast-export.git)
# - Both git and hg (Mercurial) must be installed
#
# Usage:
#   ,hg2git /path/to/mercurial/repository
#
# The script will:
# 1. Create a new Git repository in the same directory
# 2. Convert all Mercurial commits to Git commits
# 3. Convert the default Mercurial branch to 'main' in Git
# 4. Convert all other Mercurial branches to Git branches
# 5. Preserve the commit history
#
# Example:
#   # Convert a local Mercurial repository
#   ,hg2git ~/projects/my-hg-repo
#
#   # Convert current directory if it's a Mercurial repository
#   ,hg2git .
#
# Note: The original Mercurial repository (.hg directory) will remain untouched.
# The conversion creates a new Git repository (.git directory) alongside it.

# check if hg-fast-export is installed
if ! command -v hg-fast-export.sh &> /dev/null
then
    echo "hg-fast-export could not be found"
    echo "https://repo.or.cz/fast-export.git"
    exit
fi

# check if the directory to the mercurial repository is provided
if [ -z "$1" ]
then
    echo "No repository provided, please provide a path to a mercurial repository"
    exit
fi

# get absolute path of source directory
SOURCE_DIR=$(cd "$1" && pwd)

# create temporary directory for the git repo
TEMP_DIR=$(mktemp -d)
cd "$TEMP_DIR"

# initialize the git repository
git init

# set core.ignoreCase to false to handle case-sensitive filenames correctly
git config core.ignoreCase false

# export the mercurial repository to the git repository with branch mapping
# pointing -r back to the source directory
hg-fast-export.sh -r "$SOURCE_DIR" -M main --force

# remove the hg-fast-export files
rm -rf .git/hg-fast-export*

# checkout the main branch
git checkout HEAD

# create local branches from remote branches (only if there are remote branches)
if git branch -r | grep -v main > /dev/null 2>&1; then
    for branch in $(git branch -r | grep -v main)
    do
        git branch --track "${branch#origin/}" "$branch" 2>/dev/null || true
    done
fi

# move the git repository back to the source directory
mv .git "$SOURCE_DIR/"
cd "$SOURCE_DIR"

# clean up temp directory
rm -rf "$TEMP_DIR"

# checkout to update working directory
git checkout HEAD

# check if there are any commits
echo
if git rev-parse HEAD >/dev/null 2>&1; then
    echo "Repository has commits"
else
    echo "Repository is empty"
fi

echo
echo "Branches:"
git branch -a
