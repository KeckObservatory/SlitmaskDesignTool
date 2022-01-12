#!/bin/sh

PYTHONPATH="${PYTHONPATH}:DesignTool:DesignTool/smdtLibs"
export PYTHONPATH
PYTHON=`which python3`

checkIfRunning()
{
	pgrep -fl "slitmaskdesign.py $*"
}

start()
{
	RES=`checkIfRunning $*`
	if [ "x$RES" = "x" ]
	then
		echo "Starting .." $*
		#$PYTHON  slitmaskdesign.py $*        
        $PYTHON slitmaskdesign.py $*

	else
		echo "slitmaskdesign.py $* already running"
	fi
}

stop()
{
	RES=`checkIfRunning $*`
	if [ "x$RES" = "x" ]
	then
		echo "Nothing to stop"
	else
		pkill -f "slitmaskdesign.py $*"
	fi
}

status()
{
	RES=`checkIfRunning $*`
	if [ "x$RES" = "x" ]
	then
		echo "slitmaskdesign.py not running"
		echo $RES
	else
		pgrep -fl "slitmaskdesign.py $*"
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

