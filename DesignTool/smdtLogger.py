import logging
import logging.config


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


def setup_logger():
    logging.basicConfig(
        format="%(asctime)s %(levelname)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        level=logging.INFO,
        handlers=[logging.StreamHandler()],
    )
    return logging.getLogger()


SMDTLogger = setup_logger()
