import logging
logging.basicConfig(format='[%(levelname)-8s] %(message)s', level=logging.DEBUG)
version = 1

# Shouldn't have done that.. it works.. I hope
logging.VERBOSE= 17
logging.addLevelName(17, "VERBOSE")
def _verbose(msg, *args, **kwargs):
    logging.log(logging.VERBOSE, msg, *args, **kwargs)
logging.verbose = _verbose
logger = logging.getLogger()