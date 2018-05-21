#coding=utf-8
import logging
import sys
import argparse
import ctypes
import platform
TOOLSFORAI_OS_WIN = "win"
TOOLSFORAI_OS_LINUX = "linux"
TOOLSFORAI_OS_MACOS = "mac"


def _init_logger(log_level=logging.INFO):
    logger = logging.getLogger('Microsoft Visual Studio Tools for AI')
    logger.setLevel(log_level)
    logger.propagate = False
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(fmt='%(asctime)s [%(levelname)s] '
                                      '[%(name)s] %(message)s',
                                  datefmt='%H:%M:%S')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger
logger = _init_logger()

def set_options():
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--verbose", help="give more output to debug log level.", action="store_true")
    parser.add_argument("-u", "--user", help="install to the Python user install directory for your platform.",
                        action="store_true")
    parser.add_argument("--cuda80", help="forcing the installation of the dependency packages for cuda 8.0.",
                        action="store_true")
    parser.add_argument("-o", "--options",
                        help="add extra options for packages installation. --user ignored if this option is supplied.")
    args, unknown = parser.parse_known_args()
    return args, unknown

# ShellExecuteInfo
if platform.system() == "Windows":
    from ctypes.wintypes import HANDLE, BOOL, DWORD, HWND, HINSTANCE, HKEY
class ShellExecuteInfo(ctypes.Structure):
    _fields_ = [('cbSize', DWORD),
                ('fMask', ctypes.c_ulong),
                ('hwnd', HWND),
                ('lpVerb', ctypes.c_char_p),
                ('lpFile', ctypes.c_char_p),
                ('lpParameters', ctypes.c_char_p),
                ('lpDirectory', ctypes.c_char_p),
                ('nShow', ctypes.c_int),
                ('hInstApp', HINSTANCE),
                ('lpIDList', ctypes.c_void_p),
                ('lpClass', ctypes.c_char_p),
                ('hKeyClass', HKEY),
                ('dwHotKey', DWORD),
                ('hIcon', HANDLE),
                ('hProcess', HANDLE)]

    def __init__(self, **kw):
        ctypes.Structure.__init__(self)
        self.cbSize = ctypes.sizeof(self)
        for name, value in kw.items():
            setattr(self, name, value)

class SysInfo(object):
    os = None
    python = None
    gpu = False
    cuda = None
    cudnn = None
    cuda80 = False
    git = False
    mpi = None
    fail_install = []
    def __init__(self):
        pass