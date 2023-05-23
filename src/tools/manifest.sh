#!/bin/sh
# one liner for printing all files in the repo
git log --pretty=format: --name-only | sort | uniq 
