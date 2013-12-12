import logging
import inspect

logging.basicConfig(format="%(message)s")

def get_logger():
    frame = inspect.stack()[1][0]
    module = inspect.getmodule(frame)
    name = module.__name__
    return logging.getLogger(name)

log = get_logger()

def set_level(lvl):
    if isinstance(lvl, basestring):
        try:
            lvl = eval('logging.%s'%(lvl.upper()))
        except:
            log.error("invalid log level: %s", lvl)
            return False
    assert isinstance(lvl, int)
    get_logger().setLevel(lvl)
