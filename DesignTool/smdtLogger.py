import logging
import logging.config


logging.config.fileConfig('logger.conf')
SMDTLogger = logging.getLogger('SMDTLogger')


def infoLog (f):
    def ff (*args, **kargs):
        SMDTLogger.info('Calling {} with {}, {}'.format(f.__name__, args, kargs))
        return f(*args, **kargs)
    return ff
