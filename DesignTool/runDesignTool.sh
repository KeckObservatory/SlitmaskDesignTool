#!/bin/sh

PYTHONHOME="/local/anaconda3/"
PYTHON="${PYTHONHOME}/bin/python"

export PYTHONHOME 

checkIfRunning()
{
	pgrep -fl "SlitmaskDesignServer.py $*"
}

start()
{
	RES=`checkIfRunning $*`
	if [ "x$RES" = "x" ]
	then
		echo "Starting .." $*
		$PYTHON  SlitmaskDesignServer.py $*
	else
		echo "SlitmaskDesignServer.py $* already running"
	fi
}

stop()
{
	RES=`checkIfRunning $*`
	if [ "x$RES" = "x" ]
	then
		echo "Nothing to stop"
	else
		pkill -f "SlitmaskDesignServer.py $*"
	fi
}

status()
{
	RES=`checkIfRunning $*`
	if [ "x$RES" = "x" ]
	then
		echo "SlitmaskDesignServer.py not running"
		echo $RES
	else
		pgrep -fl "SlitmaskDesignServer.py $*"
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
		echo "runDesignTool.sh start|stop|restart|status"
		status 
	;;
esac





