## Installing
Valid for Ubuntu Oneiric Ocelot (11.10). Do this with root privileges (sudo -i).

1. Python setuptools and ordereddict:

        python-setuptools
        easy_install ordereddict

2. Tornado webserver framework:

        wget http://github.com/downloads/facebook/tornado/tornado-2.2.tar.gz
        tar xvzf tornado-2.2.tar.gz
        cd tornado-2.2
        python setup.py build
        sudo python setup.py install

3. distribute (needed for tornadio2):

        curl -O http://python-distribute.org/distribute_setup.py
        python distribute_setup.py

4. tornadio2 (SocketIO support for Tornado):

        wget https://github.com/MrJoes/tornadio2/tarball/master
        tar xvzf MrJoes-tornadio2*.tar.gz
        rm MrJoes-tornadio2*.tar.gz
        cd MrJoes-tornadio2*
        python setup.py build
        sudo python setup.py install


##  Running 

##### From Eclipse

Import this folder to Eclipse (with PyDev) and run JazzyServer.py from jazzy.server package:

Then point your browser to http://yoururl:8090 to create a game and play.
You can start experimenting with localhost as yoururl and use services like dyndns for usage over the internet. Make sure to forward port 8090 to the server.


##### From Command Line
    cd src/jazzy/server
    export PYTHONPATH=../../../src:$PYTHONPATH; ./JazzyServer.py



##  Developing

We use LESS (http://less-css.org) for a convenient CSS extension.

Installation instructions for Ubuntu Linux 11.04:

    sudo apt-get install ruby rubygems1.8
    sudo gem install rubygems-update
    sudo gem update rubygems 
    sudo gem install less
    sudo ln -s /var/lib/gems/1.8/bin/lessc /usr/bin/


## Credits

The awesome wood textures are made by "Ransie3" (http://ransie3.deviantart.com/), specifically downloaded from here: http://ransie3.deviantart.com/art/Patterns-21-187627358


## License
Jazzy is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as
published by the Free Software Foundation, either version 3 of the
License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program. If not, see <http://www.gnu.org/licenses/agpl.html>.
