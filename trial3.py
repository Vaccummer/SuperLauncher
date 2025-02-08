import am_store as am
import time
logger = am.get_logger('a.log')
logger.info("test", 'this is a test message', exc=Exception("this is a test exception"))
logger.warning("test")
logger.error("test")
logger.critical("test", 'this is a hahahahah')
def a():
    b()
def b():
    c()
def c():
    d()
def d():
    time.sleep(1)
    a = 1/0
a()
