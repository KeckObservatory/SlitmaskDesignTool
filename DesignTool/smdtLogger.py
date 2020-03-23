import logging
import logging.config


logging.config.fileConfig("logger.conf")
SMDTLogger = logging.getLogger("SMDTLogger")


def infoLog(f):
    """
    Decorator for debugging.
    For example:
    
    @infoLog
    def func(a,b,c):
        pass
        
    """

    def ff(*args, **kargs):
        SMDTLogger.info("Calling {} with {}, {}".format(f.__name__, args, kargs))
        return f(*args, **kargs)

    return ff
