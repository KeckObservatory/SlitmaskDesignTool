
# How to run

The file runDesignTool.sh is convenient shell script to start and stop the Slitmask Design Tool.

The Slitmask Design Tool starts the main program that acts as a web server. Optionally, a web-browser can be started at the same time. If a web-browser is manually, say from another machine then the URL http://hostname:9301 should be used, where hostname is the name of the machine running the main program.


To run the server:	

   * runDesignTool.sh start
   or, start with browser
   * runDesignTool.sh start -b  

To stop the server:

   * runDesignTool.sh stop

To check if running:

   * runDesignTool.sh status


The Slitmask Design Tool need the a configuration file (default smdt.cfg) and a parameters file (default params.cfg). These default files are in the Design directory.

The location of the parameters file is given in smdt.cfg.

To use another, customized, smdt.cfg file, start the program with:
   * runDesignTool.sh start -c <where_is_the_smdt_file>

The main python program is slitmaskdesign.py, which can be started manually if the environment variable PYTHONPATH includes the directory Design/ and Design/smdtLibs.

The URL to connect to the server is http://hostname:portNr.
The hostname is the name of the machine running the main program and portNr is defautl 9301 as given in smdt.cfg.