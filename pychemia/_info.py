__author__ = "Guillermo Avendano-Franco"
__copyright__ = "Copyright 2015"
__version__ = "0.1.1"
__email__ = "gtux.gaf@gmail.com"
__status__ = "Development"
__date__ = "June 26, 2015"


class Version:

    @staticmethod
    def full_version():
        return 'PyChemia Version='+__version__+' from='+__date__

    def __init__(self):
        pass
