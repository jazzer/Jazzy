#!/bin/sh

# This file is supposed to do some good to the JS and CSS files
# by minimizing them for performance's sake.


# where are we? (thanks http://hintsforums.macworld.com/showpost.php?p=455557&postcount=16)

## Linux
LSOF=$(lsof -p $$ | grep -E "/"$(basename $0)"$")
MY_PATH=$(echo $LSOF | sed -r s/'^([^\/]+)\/'/'\/'/1 2>/dev/null)
if [ $? -ne 0 ]; then
## OSX
  MY_PATH=$(echo $LSOF | sed -E s/'^([^\/]+)\/'/'\/'/1 2>/dev/null)
fi

dir=$(dirname $MY_PATH)


# ====================
#     JavaScript
# ====================
#rhino "$dir/jshint.js" "$dir/../jsclient/js/jazzy_logic.js" > "$dir/../jsclient/js/jazzy_logic.min.js"
yui-compressor "$dir/../jsclient/js/jazzy_board.js" > "$dir/../jsclient/js/jazzy_board.min.js"
yui-compressor "$dir/../jsclient/js/jazzy_logic.js" > "$dir/../jsclient/js/jazzy_logic.min.js" # current fails, therefore:
cp "$dir/../jsclient/js/jazzy_logic.js" "$dir/../jsclient/js/jazzy_logic.min.js"
yui-compressor "$dir/../jsclient/js/jazzy_admin.js" > "$dir/../jsclient/js/jazzy_admin.min.js"

# ====================
#     CSS
# ====================
# loop all less files
for file in $( find "$dir/../jsclient/css" -iname "*.less" )
do
	filename=$(basename $file)
	filename=${filename%.*}
	lessc "$file" > "$dir/../jsclient/css/$filename.css"
done
