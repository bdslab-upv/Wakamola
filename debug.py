import logging
import time


def timeit(method):
    # Measure time decorator
    logger = logging.getLogger("timeit")
    logger.setLevel(logging.INFO)

    def timed(*args, **kw):
        ts = time.time()
        result = method(*args, **kw)
        te = time.time()
        logger.info(f"{method.__name__} = {round(te - ts, 2)}s")
        return result

    return timed
