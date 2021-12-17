#!/bin/sh

PYTHONPATH="${PYTHONPATH}:DesignTool:DesignTool/smdtLibs"
export PYTHONPATH
PYTHON=`which python3`

checkIfRunning()
{
	pgrep -fl "slitmaskDesignServer.py $*"
}

start()
{
	RES=`checkIfRunning $*`
	if [ "x$RES" = "x" ]
	then
		echo "Starting .." $*
		#$PYTHON  slitmaskDesignServer.py $*        
        $PYTHON slitmaskdesign.py $*

	else
		echo "slitmaskDesignServer.py $* already running"
	fi
}

stop()
{
	RES=`checkIfRunning $*`
	if [ "x$RES" = "x" ]
	then
		echo "Nothing to stop"
	else
		pkill -f "slitmaskDesignServer.py $*"
	fi
}

status()
{
	RES=`checkIfRunning $*`
	if [ "x$RES" = "x" ]
	then
		echo "slitmaskDesignServer.py not running"
		echo $RES
	else
		pgrep -fl "slitmaskDesignServer.py $*"
	fi
}

CMD=$1
shift

case x$CMD in
	xstart)
		start $*
	;;
	xstop)
		stop $*
	;;
	xstatus)
		status $*
	;;
	xrestart)
		stop $*
		sleep 2
		start $*
	;;
	*)
		echo "runDesignTool.sh start|stop|restart|status [-b]"
		echo "-b: start browser"
		status 
	;;
esac

