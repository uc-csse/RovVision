#!/bin/bash
rsync -avzu -e ssh  --exclude=".git/" --include="*/" --include="*.py" --exclude="*" . labuser@cs18018hr:projects/bluerov/

