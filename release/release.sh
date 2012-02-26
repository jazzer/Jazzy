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
# generate from coffee-script
cd "$dir/coffee-script/"
#java -jar jcoffeescript.jar < "$dir/../src/jsclient/js/jazzy_board.coffee" > "$dir/../src/jsclient/js/jazzy_board.js"
#java -jar jcoffeescript.jar < "$dir/../src/jsclient/js/jazzy_board.coffee" > "$dir/../src/jsclient/js/jazzy_board.js"
#java -jar jcoffeescript.jar < "$dir/../src/jsclient/js/jazzy_board.coffee" > "$dir/../src/jsclient/js/jazzy_board.js"
# minify
cd "$dir/../src/jazzy/jsclient/js/"
yui-compressor "jazzy_board.js" > "jazzy_board.min.js"
yui-compressor "jazzy_logic.js" > "jazzy_logic.min.js" # currently fails, therefore:
cp "jazzy_logic.js" "jazzy_logic.min.js"
yui-compressor "jazzy_admin.js" > "jazzy_admin.min.js"

# ====================
#     CSS
# ====================
# loop all less files
cd "$dir/../src/jazzy/jsclient/css"
for file in $( find . -iname "*.less" )
do
	filename=$(basename $file)
	filename=${filename%.*}
	lessc "$file" > "$filename.css"
done

cd $dir

# update copyright info
#find . -name '*.js' | xargs perl -pi -e 's/Copyright \(c\) 2011/Copyright (c) 2011-2012/g'
#find . -name '*.py' | xargs perl -pi -e 's/Copyright \(c\) 2011/Copyright (c) 2011-2012/g'
#find . -name '*.html' | xargs perl -pi -e 's/Copyright \(c\) 2011/Copyright (c) 2011-2012/g'

