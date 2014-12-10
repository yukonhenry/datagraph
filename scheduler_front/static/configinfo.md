#### Dojo, dgrid.io must be installed

Instructions are for Ubuntu

1. cd static (this directory)
2. Install Dojo
  - wget http://download.dojotoolkit.org/release-1.10.3/dojo-release-1.10.3.tar.gz
  - tar -xvf dojo-release-1.10.3.tar.gz --strip 1 
3. Install Dgrid (dgrid.io)
  - sudo add-apt-resository ppa:chris-lea/node.js  
  - sudo apt-get update  
  - sudo apt-get install nodejs
  - sudo npm -g install bower
  - create .bowerrc file with following content: {"directory": "."} and place in ~ directory
  - cd static
  - bower install dgrid
  - references
    * http://dgrid.io/
    * http://askubuntu.com/questions/519189/how-can-i-get-jshint-to-work/531943#531943
    * http://stackoverflow.com/questions/7214474/how-to-keep-up-with-the-latest-versions-of-nodejs-in-ubuntu-ppa-compiling
5. Install Nginx (or other hosting server)
  - Modify /etc/nginx/site-defaults/default (description tbd)
  - sudo service nginx restart
