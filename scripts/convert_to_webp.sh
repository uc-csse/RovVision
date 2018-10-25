#!/bin/bash
for f in $(find . -name "*.ppm" -type f); do 
	echo $f
	convert $f  /tmp/tmp.png ; 
	cwebp -quiet -mt -q 90  /tmp/tmp.png -o ${f%.*}.webp && rm $f
done
rm /tmp/tmp.png
