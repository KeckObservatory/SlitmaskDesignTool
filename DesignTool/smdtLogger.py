import logging
import logging.config

logging.config.fileConfig('logger.conf')
SMDTLogger = logging.getLogger('SMDTLogger')