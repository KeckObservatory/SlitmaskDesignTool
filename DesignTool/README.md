
# How to run

SlitmaskDesignServer.py is the main entry point for the server.
The client is the web browser running the HTML and Javascript.

To run the server:	

   * python3  SlitmaskDesignServer.py 
	
Either set the current directory must be this directory or 
set PYTHONPATH to include this directory.

If you have a configuration file different from smdr.cfg, it can be specified on the 
command line as -c

If there are issue with automatically determining the host name (Error 8), you can 
specify the host on the command line:

   * python3 SlitmaskDesignServer.py -host 127.0.0.1

The file smdt.cfg defines the configuration parameters, including the port number for the server.


On the client side, start the browser and enter the URL:
	
   * on local machine
   
      http://localhost:50080
      
   * on remote machine
      http:/ip-of-server:50080
      
Use 50080 or another port number given in the configuration file (smdt.cfg).