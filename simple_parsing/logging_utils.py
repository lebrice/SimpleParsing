import logging
from pathlib import Path

def get_logger(name: str) -> logging.Logger:
        """ Gets a logger for the given file. Sets a nice default format. 
        TODO: figure out if we should add handlers, etc. 
        """
        try:
            p = Path(name)
            if p.exists():
                name = str(p.absolute().relative_to(Path.cwd()).as_posix())
        except:
            pass
        logger = logging.getLogger(name)
        # logger.addHandler(TqdmLoggingHandler())
        return logger
