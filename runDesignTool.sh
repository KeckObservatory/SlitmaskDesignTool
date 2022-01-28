#!/bin/sh

my_realpath() {
	BNAME=`basename $1`
    DNAME=`dirname $1`
    FDIR=`(cd $DNAME; pwd)`
    echo $FDIR/$BNAME
}

DIR0=`my_realpath $0`
PROGBASE=`dirname $DIR0`

PYTHONPATH="${PYTHONPATH}:${PROGBASE}/DesignTool:${PROGBASE}/DesignTool/smdtLibs"
export PYTHONPATH
PYTHON=`which python3`

checkIfRunning()
{
	pgrep -lf "DesignTool/slitmaskdesign.py*"
}

start()
{
	RES=`checkIfRunning`
	if [ "x$RES" = "x" ]
	then
		echo "Starting ..." $*
		#$PYTHON  slitmaskdesign.py $*        
        $PYTHON ${PROGBASE}/DesignTool/slitmaskdesign.py $*
	else
		echo "slitmaskdesign.py $* already running"
	fi
}

stop()
{
	RES=`checkIfRunning`
	if [ "x$RES" = "x" ]
	then
		echo "Nothing to stop"
	else
		pkill -f "DesignTool/slitmaskdesign.py"
	fi
}

status()
{
	RES=`checkIfRunning`
	if [ "x$RES" = "x" ]
	then
		echo "slitmaskdesign.py not running"
		echo $RES
	else
		echo "slitmasdesign is running"
		ps -ef | fgrep slitmaskdesign.py | fgrep -v grep
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

