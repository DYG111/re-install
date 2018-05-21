#coding=utf-8
from init import TOOLSFORAI_OS_LINUX, TOOLSFORAI_OS_WIN, TOOLSFORAI_OS_MACOS
from init import SysInfo, ShellExecuteInfo
from init import logger

import argparse
import ctypes
import os
import platform
import re
import subprocess
import sys
import yaml
if platform.system() == "Windows":
    import winreg

# detect
def detect_os():
    os_name = platform.platform(terse=True)
    os_bit = platform.architecture()[0]
    is_64bit = (os_bit == "64bit")
    logger.info("OS: {0}, {1}".format(os_name, os_bit))

    if (os_name.startswith("Windows")):
        SysInfo.os = TOOLSFORAI_OS_WIN
        if not os_name.startswith("Windows-10"):
            logger.warning(
                "We recommend Windows 10 as the primary development OS, other Windows versions are not fully supported.")
    elif (os_name.startswith("Linux")):
        SysInfo.os = TOOLSFORAI_OS_LINUX
    elif (os_name.startswith("Darwin")):
        SysInfo.os = TOOLSFORAI_OS_MACOS
        is_64bit = sys.maxsize > 2 ** 32
    else:
        logger.error("Your OS({0}-{1}) can't be supported! Only Windows, Linux and MacOS can be supported now.".format(os_name, os_bit))
        return False
    if not is_64bit:
        logger.error("Your OS is not 64-bit OS. Now only 64-bit OS is supported.")
        return False
    return True

def detect_gpu():
    gpu_detector_name = 'gpu_detector_' + SysInfo.os
    if (SysInfo.os == TOOLSFORAI_OS_WIN):
        gpu_detector_name = gpu_detector_name + '.exe'
    gpu_detector_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "tools", gpu_detector_name)

    if not (os.path.isfile(gpu_detector_path)):
        logger.error(
            'Not find GPU detector. Please make sure {0} is in the same directory with the installer script.'.format(
                gpu_detector_name))
        return False
    SysInfo.gpu, return_stdout = _run_cmd(gpu_detector_path, return_stdout=True)
    if not SysInfo.gpu:
        return_stdout = 'None'
    logger.info('NVIDIA GPU: {0}'.format(return_stdout))
    return True

def detect_python_version():
    py_architecture = platform.architecture()[0]
    py_version = ".".join(map(str, sys.version_info[0:2]))
    py_full_version = ".".join(map(str, sys.version_info[0:3]))
    SysInfo.python = py_version.replace('.', '')
    logger.debug("In detect_python_version(), sys_info['python']: {0}".format(SysInfo.python))
    logger.info("Python: {0}, {1}".format(py_full_version, py_architecture))
    if not (_version_compare("3.5", py_version) and py_architecture == '64bit'):
        logger.error("64-bit Python 3.5 or higher is required to run this installer."
                     " We recommend latest Python 3.5 (https://www.python.org/downloads/release/python-355/).")
        return False
    return True

def detect_git():
    res = _run_cmd("git", ["--version"])
    SysInfo.git = res
    if res:
        logger.info("Git: {0}".format(res))
    else:
        logger.info("Git: {0} (Git is needed, otherwise some dependency packages can't be installed.)".format(res))

def detect_vs():
    vs = []
    vs_2015_path = _registry_read(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\VisualStudio\14.0",
                                  "InstallDir")
    if (vs_2015_path and os.path.isfile(os.path.join(vs_2015_path, "devenv.exe"))):
        vs.append("VS2015")
    vs_2017_path = _registry_read(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\VisualStudio\SxS\VS7",
                                  "15.0")
    if (vs_2017_path and os.path.isfile(os.path.sep.join([vs_2017_path, "Common7", "IDE", "devenv.exe"]))):
        vs.append("VS2017")
    if (len(vs) == 0):
        logger.warning("Not detect Visual Studio 2017 or 2015! We recommend Visual Studio 2017, "
                       "please manually download and install Visual Studio 2017 form https://www.visualstudio.com/downloads/.")
    else:
        logger.info("Visual Studio: {0}".format(" ".join(vs)))

def detect_cuda():
    if (SysInfo.os == TOOLSFORAI_OS_WIN or SysInfo.os == TOOLSFORAI_OS_LINUX):
        # return detect_cuda_()
        status, stdout = _run_cmd("nvcc", ["-V"], True)
        if status and re.search(r"release\s*8.0,\s*V8.0", stdout):
            SysInfo.cuda = "8.0"
            logger.info("CUDA: {0}".format(SysInfo.cuda))
            if SysInfo.cuda80:
                logger.warning(
                    "Detect parameter '--cuda80', the installer script will be forced to install dependency package for CUDA 8.0.")
                return True
            else:
                logger.warning("We recommend CUDA 9.0 (https://developer.nvidia.com/cuda-toolkit)."
                               "If you want to install dependency package for CUDA 8.0, please run the installer script with '--cuda80' again.")
                return False
        elif status and re.search(r"release\s*9.0,\s*V9.0", stdout):
            SysInfo.cuda = "9.0"
            logger.info("CUDA: {0}".format(SysInfo.cuda))
        else:
            SysInfo.cuda = "9.0"
            logger.warning("Not detect CUDA! We recommend CUDA 9.0 (https://developer.nvidia.com/cuda-toolkit). "
                           "The installer script will install dependency package for CUDA 9.0 by default.")
        if SysInfo.cuda80:
            SysInfo.cuda = "8.0"
            logger.warning(
                "Detect parameter '--cuda80', the installer script will be forced to install dependency package for CUDA 8.0.")
        return True
    else:
        return True

def detect_cudnn():
    if (SysInfo.os == TOOLSFORAI_OS_WIN):
        detect_cudnn_win()

def detect_cudnn_win():
    if SysInfo.cuda == "8.0":
        required_cndunn = {'6': 'cudnn64_6.dll', '7': 'cudnn64_7.dll'}
    else:
        required_cndunn = {'7': 'cudnn64_7.dll'}
    cmd = r"C:\Windows\System32\where.exe"
    for version, dll in required_cndunn.items():
        args = [dll]
        status, cudnn = _run_cmd(cmd, args, True)
        if status and next(filter(os.path.isfile, cudnn.split('\n')), None):
            SysInfo.cudnn = version
            logger.info("cuDNN: {0}".format(version))
    if not SysInfo.cudnn:
        logger.warning("Not detect cuDNN! We recommand cuDNN 7, please download and install cuDNN 7 from https://developer.nvidia.com/rdp/cudnn-download.")

def detect_mpi_win():
    target_version = "7.0.12437.6"
    mpi_path = _registry_read(winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\MPI", "InstallRoot")
    if (mpi_path and os.path.isfile(os.path.sep.join([mpi_path, "bin", "mpiexec.exe"]))):
        SysInfo.mpi = _registry_read(winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\MPI", "Version")
    if SysInfo.mpi:
        logger.info("MPI: {0}".format(SysInfo.mpi))
        if not _version_compare(target_version, SysInfo.mpi):
            logger.warning("CNTK suggests MPI version to be {0}, please manually upgrade MPI.".format(target_version))
            return False
        return True
    else:
        logger.warning("Not detect MPI, please manually download and isntall MPI.")
        return False

def detect_visualcpp_runtime_win():
    pattern = re.compile(
        "(^Microsoft Visual C\+\+ 201(5|7) x64 Additional Runtime)|(^Microsoft Visual C\+\+ 201(5|7) x64 Minimum Runtime)")
    items = [(winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
             (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
             (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall")]
    for hkey, keypath in items:
        try:
            current_key = winreg.OpenKey(hkey, keypath)
            for subkey in _registry_subkeys(hkey, keypath):
                display_name = _registry_read(current_key, subkey, "DisplayName")
                if (display_name and pattern.match(display_name)):
                    logger.info("Detect Visual C++ runtime already installed.")
                    return True
            winreg.CloseKey(current_key)
        except WindowsError:
            pass
    logger.warning("Not detect Visual C++ runtime.")
    return False

def module_exists(module_name):
    try:
        from pkgutil import iter_modules
        return module_name in (name for loader, name, ispkg in iter_modules())
    except:
        return False


# read, write and delete registry
def _registry_read(hkey, keypath, value_name):
    try:
        registry_key = winreg.OpenKey(hkey, keypath)
        value, _ = winreg.QueryValueEx(registry_key, value_name)
        winreg.CloseKey(registry_key)
        return value
    except Exception as e:
        logger.debug("Fail to read registry key: {0}, value: {1}, unexpected error: {2}".format(keypath, value_name, e))
        return None

def _registry_subkeys(hkey, keypath):
    key = winreg.OpenKey(hkey, keypath, 0, winreg.KEY_READ)
    i = 0
    while True:
        try:
            subkey = winreg.EnumKey(key, i)
            yield subkey
            i += 1
        except WindowsError as e:
            break

def _registry_write(hkey, keypath, name, value):
    try:
        registry_key = winreg.CreateKeyEx(hkey, keypath)
        winreg.SetValueEx(registry_key, name, 0, winreg.REG_SZ, value)
        winreg.CloseKey(registry_key)
        return True
    except Exception as e:
        logger.debug("Fail to write registry key: {0}, name: {1}, value: {2}, unexpected error: {3}".format(keypath, name, value, e))
        return False

def _registry_delete(hkey, keypath, name):
    try:
        registry_key = winreg.OpenKey(hkey, keypath, 0, winreg.KEY_SET_VALUE)
        winreg.DeleteValue(registry_key, name)
        winreg.CloseKey(registry_key)
        return True
    except Exception as e:
        logger.debug("Fail to delete registry key: {0}, name: {1},  unexpected error: {2}".format(keypath, name, e))
        return False


# run cmd
def _run_cmd(cmd, args=[], return_stdout=False):
    try:
        p = subprocess.run([cmd, *args], stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        stdout = p.stdout.strip()
        stderr = p.stderr.strip()
        status = p.returncode == 0
        logger.debug("========== {:^30} ==========".format("%s : stdout" % cmd))
        for line in filter(lambda x: x.strip(), p.stdout.split('\n')):
            logger.debug(line)
        logger.debug("========== {:^30} ==========".format("%s : stdout end" % cmd))
        logger.debug("========== {:^30} ==========".format("%s : stderr" % cmd))
        for line in filter(lambda x: x.strip(), p.stderr.split('\n')):
            logger.debug(line)
        logger.debug("========== {:^30} ==========".format("%s : stderr end" % cmd))
    except Exception as e:
        logger.debug("Fail to execute command: {0}, unexpected error: {1}".format(cmd, e))
        status = False
        stdout = ""
    if return_stdout:
        return status, stdout
    else:
        return status

def _wait_process(processHandle, timeout=-1):
    try:
        ret = ctypes.windll.kernel32.WaitForSingleObject(processHandle, timeout)
        logger.debug("Wait process return value: %d" % ret)
    except Exception as e:
        logger.debug("Fail to wait process, unexpected error: {0}".format(e))
    finally:
        ctypes.windll.kernel32.CloseHandle(processHandle)

def _run_cmd_admin(cmd, param, wait=True):
    try:
        executeInfo = ShellExecuteInfo(fMask=0x00000040, hwnd=None, lpVerb='runas'.encode('utf-8'),
                                       lpFile=cmd.encode('utf-8'), lpParameters=param.encode('utf-8'),
                                       lpDirectory=None,
                                       nShow=5)
        if not ctypes.windll.shell32.ShellExecuteEx(ctypes.byref(executeInfo)):
            raise ctypes.WinError()
        if wait:
            _wait_process(executeInfo.hProcess)
    except Exception as e:
        # logger.error("Fail to run command {0} as admin, unexpected error: {1}".format(cmd, e))
        logger.error("Fail to run command {0} as admin, unexpected error! Please try to run installer script again!".format(cmd))


# download, extract file
def _download_file(url, local_path):
    logger.info("Downloading {0} ...".format(url))
    try:
        import urllib.request
        import ssl
        myssl = ssl.create_default_context()
        myssl.check_hostname = False
        myssl.verify_mode = ssl.CERT_NONE
        with urllib.request.urlopen(url, context=myssl) as fin, \
                open(local_path, 'ab') as fout:
            fout.write(fin.read())
        return True
    except:
        logger.error("Fail to download {0}. Error: {1}".format(url, sys.exc_info()))
        return False

def _unzip_file(file_path, target_dir):
    logger.info("Unzipping {0} to {1} ...".format(file_path, target_dir))
    try:
        import zipfile
        with zipfile.ZipFile(file_path) as zip_file:
            if os.path.isdir(target_dir):
                pass
            else:
                os.makedirs(target_dir)
            for names in zip_file.namelist():
                zip_file.extract(names, target_dir)
        return True
    except:
        logger.error("Fail to unzip. Error: ", sys.exc_info())
        return False

def _extract_tar(file_path, target_dir):
    logger.info("Extracting {0} to {1} ...".format(file_path, target_dir))
    try:
        import tarfile
        with tarfile.open(file_path) as tar:
            tar.extractall(path=target_dir)
    except:
        logger.error("Fail to extract. Error: ", sys.exc_info())
        return False
    return True


# version
def _version_compare(ver1, ver2):
    to_version = lambda ver: tuple([int(x) for x in ver.split('.') if x.isdigit()])
    return to_version(ver1) <= to_version(ver2)

def _get_cntk_version(cntk_root):
    logger.debug("In _get_cntk_version(), cntk_root: {0}".format(cntk_root))
    version = ''
    version_file = os.path.join(cntk_root, "cntk", "version.txt")

    if os.path.isfile(version_file):
        with open(version_file) as fin:
            version = fin.readline().strip()
    logger.debug("In _get_cntk_version(), find cntk_version: {0}".format(version))
    return version

# env
def _update_pathenv_win(path, add):
    path_value = _registry_read(winreg.HKEY_CURRENT_USER, "Environment", "PATH")
    logger.debug("Before update, PATH: {0}".format(path_value))

    if add:
        if path in path_value:
            return
        path_value = path + ";" + path_value
        os.environ["PATH"] = path + ";" + os.environ.get("PATH", "")
    else:
        path_value = path_value.replace(path + ";", "")
        os.environ["PATH"] = os.environ["PATH"].replace(path + ";", "")
    _registry_write(winreg.HKEY_CURRENT_USER, "Environment", "PATH", path_value)

def delete_env(name):
    if name in os.environ:
        logger.debug("Delete environment variable: {0}".format(name))
        return _registry_delete(winreg.HKEY_CURRENT_USER, "Environment", name)
    else:
        logger.debug("Environment variable {0} doesn't exist.".format(name))
        return True

def set_ownership_as_login(target_dir):
    if (SysInfo.os == TOOLSFORAI_OS_WIN):
        return
    try:
        import grp
        import pwd
        import getpass
        if ((not os.path.isdir(target_dir)) or (not os.path.exists(target_dir))):
            return
        real_user = os.getlogin()
        real_group = grp.getgrgid(pwd.getpwnam(real_user).pw_gid).gr_name
        if ((not real_user) or (not real_group)):
            return
        if (real_user != getpass.getuser()):
            _run_cmd('chown', ['-R', '{0}:{1}'.format(real_user, real_group), target_dir])
    except:
        pass

def fix_directory_ownership():
    # On Linux, if users install with "sudo", then ~/.toolsforai will have wrong directory ownership.
    target_dir = os.path.sep.join([os.path.expanduser('~'), '.toolsforai'])
    set_ownership_as_login(target_dir)

def set_options():
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--verbose", help="give more output to debug log level.", action="store_true")
    parser.add_argument("-u", "--user", help="install to the Python user install directory for your platform.",
                        action="store_true")
    parser.add_argument("--cuda80", help="forcing the installation of the dependency packages for cuda 8.0.",
                        action="store_true")
    parser.add_argument("-o", "--options",
                        help="add extra options for packages installation. --user ignored if this option is supplied.")

def rd_config():
    config_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "config", "config.yaml")
    with open(config_path) as f:
        pkg_info = yaml.load(f)
        return pkg_info