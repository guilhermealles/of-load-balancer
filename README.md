The controller implementation is in the pox/ directory. Topologies used for testing are on the
topologies/ directory.

IMPORTANT: The install.sh script assumes that the POX controller is installed under the
current user's home directory. To use the install script, one needs to pass the directory
containing controller code to the script. Assuming the repository's root directory is the
current directory, then:
    $ ./install.sh pox/
should do the trick. To run the POX controller, after installing it:
    $ cd $HOME/pox && ./pox.py log.level --DEBUG load_balancer
