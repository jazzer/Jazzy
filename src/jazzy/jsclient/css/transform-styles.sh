#!/bin/sh

# where are we? (thanks http://hintsforums.macworld.com/showpost.php?p=455557&postcount=16)

## Linux
LSOF=$(lsof -p $$ | grep -E "/"$(basename $0)"$")
MY_PATH=$(echo $LSOF | sed -r s/'^([^\/]+)\/'/'\/'/1 2>/dev/null)
if [ $? -ne 0 ]; then
## OSX
  MY_PATH=$(echo $LSOF | sed -E s/'^([^\/]+)\/'/'\/'/1 2>/dev/null)
fi

dir=$(dirname $MY_PATH)

# loop all less files
for file in $( find "$dir" -iname "*.less" )
do
	filename=$(basename $file)
	filename=${filename%.*}
	lessc "$file" > $filename".css"
done
