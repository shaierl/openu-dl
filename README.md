# Open-u courses video downloader (And Encoder)

Requirments:
------------
  * python >= 2.7 (python3 is not supported)
  * libmimms2 requirments:
    * python-progressbar - <https://pypi.python.org/pypi/progressbar/2.3-dev>
    * libmms (>= 0.4) - <http://sourceforge.net/projects/libmms>
  * mencoder - <https://help.ubuntu.com/community/mencoder>

Usage:
------
    ./openu-dl.py <threads> <openu-user> <openu-password> <openu-id (T.Z)> <openu-semester> <openu-course>
    Example: ./openu-dl.py 30 uberuser Pass123 123456789 2015a 20301

Checkout:
---------
When checking out, please make sure to init submodule, you can do it either with --recursive flag:

    git clone --recursive https://github.com/DxCx/openu-dl.git
Or Manually:

    git clone https://github.com/DxCx/openu-dl.git
    git submodule init
    git submodule update --recursive
Thanks:
------
  * Itay Perl (libmimms2) - <https://github.com/itayperl/mimms2>
