#coding=utf-8
from init import TOOLSFORAI_OS_LINUX, TOOLSFORAI_OS_WIN, TOOLSFORAI_OS_MACOS
from init import SysInfo
from init import logger
import utils

import importlib
import os
import shutil
import subprocess
import sys

def install_cntk(target_dir):
    logger.info("Begin to install CNTK(BrainScript) ...")
    if SysInfo.os != TOOLSFORAI_OS_WIN and SysInfo.os != TOOLSFORAI_OS_LINUX:
        logger.warning("CNTK(BrainScript) is not supported on your OS, we recommend 64-bit Windows-10 OS or 64-bit Linux OS.")
        # fail_install.append("CNTK(BrainScript)")
        return False
    if SysInfo.cuda == "8.0":
        ver = "2.3.1"
    else:
        ver = "2.5.1"
    target_version = 'CNTK-{0}'.format(ver.replace('.', '-'))
    logger.debug("In install_cntk(), target_version: {0}".format(target_version))
    version = utils._get_cntk_version(target_dir)
    if target_version == version:
        logger.info('CNTK(BrainScript)-{0} is already installed.'.format(ver))
        return True
    logger.debug('In install_cntk(), target_dir: {0}'.format(target_dir))
    cntk_root = os.path.join(target_dir, 'cntk')
    if os.path.isdir(cntk_root):
        try:
            shutil.rmtree(cntk_root)
        except:
            logger.error('Fail to install CNTK(BrainScript), the error message: can not remove old version in directory {0}.'
                         'Please manually remove old version, and run the installer script again.'.format(cntk_root))
            # fail_install.append("CNTK(BrainScript)")
            return False
    if not os.path.isdir(target_dir):
        try:
            os.makedirs(target_dir)
        except:
            logger.error('Fail to install CNTK(BrainScript), the error message: can not create directory {0}.'
                         'Please check if there is permission for creating directory.'.format(target_dir))
            # fail_install.append("CNTK(BrainScript)")
            return False
    cntk_file_name = "{}-{}-64bit-{}.{}".format(target_version, "Windows" if SysInfo.os == TOOLSFORAI_OS_WIN else "Linux",
                                                "GPU" if SysInfo.gpu else "CPU-Only", "zip" if SysInfo.os == TOOLSFORAI_OS_WIN else "tar.gz")
    logger.debug("In install_cntk(), cntk_file_name: {0}".format(cntk_file_name))
    cntk_url = "https://cntk.ai/BinaryDrop/{0}".format(cntk_file_name)
    logger.debug("In install_cntk(), cntk_url: {0}".format(cntk_url))
    cntk_file_path = os.path.join(target_dir, cntk_file_name)
    logger.debug("In install_cntk(), cntk_file_path: {0}".format(cntk_file_path))

    if SysInfo.os == TOOLSFORAI_OS_WIN:
        download_dir = cntk_file_path
    elif SysInfo.os == TOOLSFORAI_OS_LINUX:
        download_dir = os.path.join(r"/tmp", cntk_file_name)
    skip_downloading = False
    if not skip_downloading:
        if not utils._download_file(cntk_url, download_dir):
            logger.error('Fail to install CNTK(BrainScript), the error message: cannot download {0}.'
                         'Please check your network.'.format(cntk_url))
            # fail_install.append("CNTK(BrainScript)")
            return False

    if (not (
    utils._unzip_file(download_dir, target_dir) if SysInfo.os == TOOLSFORAI_OS_WIN else utils._extract_tar(download_dir, target_dir))):
        logger.error('Fail to install CNTK(BrainScript), the error message: cannot decompress the downloaded package.')
        # fail_install.append("CNTK(BrainScript)")
        return False

    if not skip_downloading:
        if os.path.isfile(download_dir):
            os.remove(download_dir)

    if (SysInfo.os == TOOLSFORAI_OS_WIN):
        suc = install_cntk_win(cntk_root)
    else:
        suc = install_cntk_linux(cntk_root)

    version = utils._get_cntk_version(target_dir)
    if (suc and (target_version == version)):
        logger.info("Install CNTK(BrainScript) successfully!")
        logger.warning("Please open a new terminal to make the updated Path environment variable effective.")
        return True
    else:
        logger.error("Fail to install CNTK(BrainScript).")
        logger.warning("Please manually install {0} and update PATH environment.".format(target_version))
        logger.warning("You can reference this link based on your OS: https://docs.microsoft.com/en-us/cognitive-toolkit/Setup-CNTK-on-your-machine")
        # fail_install.append("CNTK(BrainScript)")
        return False
    return True

def install_cntk_linux(cntk_root):
    logger.warning("CNTK(BrainScript) V2 on Linux requires C++ Compiler and Open MPI. "
                   "Please refer to https://docs.microsoft.com/en-us/cognitive-toolkit/Setup-Linux-Binary-Manual")
    bashrc_file_path = os.path.sep.join([os.path.expanduser('~'), '.bashrc'])
    content = ''
    with open(bashrc_file_path, 'r') as bashrc_file:
        content = bashrc_file.read()

    with open(bashrc_file_path, 'a+') as bashrc_file:
        CNTK_PATH = '{0}/cntk/bin'.format(cntk_root)
        CNTK_PATH_EXPORT = 'export PATH={0}:$PATH'.format(CNTK_PATH)
        if not (CNTK_PATH_EXPORT in content):
            bashrc_file.write('{0}\n'.format(CNTK_PATH_EXPORT))

        CNTK_LD_LIBRARY_PATH = '{0}/cntk/lib:{0}/cntk/dependencies/lib'.format(cntk_root)
        CNTK_LD_LIBRARY_PATH_EXPORT = 'export LD_LIBRARY_PATH={0}:$LD_LIBRARY_PATH'.format(CNTK_LD_LIBRARY_PATH)
        if not (CNTK_LD_LIBRARY_PATH_EXPORT in content):
            bashrc_file.write('{0}\n'.format(CNTK_LD_LIBRARY_PATH_EXPORT))

    return True

def install_cntk_win(cntk_root):
    suc = True
    try:
        utils._update_pathenv_win(os.path.join(cntk_root, "cntk"), True)
        if (not utils.detect_mpi_win()):
            mpi_exe = os.path.sep.join([cntk_root, "prerequisites", "MSMpiSetup.exe"])
            logger.debug("MPI exe path: %s" % mpi_exe)
            logger.info("Begin to install MPI ...")
            utils._run_cmd_admin(mpi_exe, "-unattend")
            if (utils.detect_mpi_win()):
                logger.info("Install MPI successfully.")
            else:
                suc = False
                logger.error("Fail to install MPI. Please manually install MPI >= 7.0.12437.6")

        if (not utils.detect_visualcpp_runtime_win()):
            vc_redist_exe = os.path.sep.join([cntk_root, "prerequisites", "VS2015", "vc_redist.x64.exe"])
            logger.debug("VC redist exe path: {0}".format(vc_redist_exe))
            logger.info("Begin to install Visual C++ runtime ...")
            utils._run_cmd_admin(vc_redist_exe, "/install /norestart /passive")
            if (utils.detect_visualcpp_runtime_win()):
                logger.info("Install Visual C++ runtime successfully.")
                logger.warning(" Please manually install Visual C++ Redistributable Package for Visual Studio 2015 or 2017.")
            else:
                suc = False
                logger.error("Fail to install Visual C++ runtime.")
    except:
        suc = False
        logger.error("Fail to install CNTK(BrainScript). The error massage: {0}".format(sys.exc_info()))

    return suc

# pip install package
def pip_install_package(name, options, version, pkg=None):
    try:
        if not pkg:
            if version:
                if version.strip()[0] == "<" or version.strip()[0] == ">":
                    pkg = "{0}{1}".format(name, version)
                else:
                    pkg = "{0} == {1}".format(name, version)
            else:
                pkg = name
                version = ""
        if not version:
            version = ""
        logger.info("Begin to pip-install {0} {1} ...".format(name, version))
        logger.debug("pkg : {0}".format(pkg))
        res = -1
        res = subprocess.check_call([sys.executable, '-m', 'pip', 'install', *options, "-q", pkg])
        if res != 0:
            logger.error("Fail to pip-install {0}.".format(name))
            SysInfo.fail_install.append("%s %s" % (name, version))
        else:
            logger.info("Pip-install {0} {1} successfully!".format(name, version))
        return res == 0
    except Exception as e:
        # logger.error("Fail to pip-install {0}, unexpected error: {0}".format(name, e))
        logger.error("Fail to pip-install {0}, unexpected error! Please try to run installer script again!".format(name))
        SysInfo.fail_install.append("%s %s" % (name, version))
        return False

def pip_uninstall_packge(name, options, version):
    try:
        if not version:
            version = ""
        logger.info("Begin to pip-uninstall {0} {1} ...".format(name, version))
        options_copy = options.copy()
        if len(options_copy) != 0 and options_copy[0] == "--user":
            options_copy.pop(0)
        res = -1
        res = subprocess.check_call([sys.executable, '-m', 'pip', 'uninstall', *options_copy, "-y", "-q", name])
        if res != 0:
            logger.error("Fail to pip-uninstall {0}.".format(name))
        else:
            logger.info("Pip-uninstall {0} {1} successfully!".format(name, version))
        return res == 0
    except Exception as e:
        # logger.error("Fail to pip-uninstall {0}, unexpected error: {1}".format(name, e))
        logger.error("Fail to pip-uninstall {0}, unexpected error! Please try to run installer script again!".format(name))
        return False

def parse_pkg_name(pkg_info):
    name = ""
    if isinstance(pkg_info["name"], str):
        name = pkg_info["name"]
    else:
        if not SysInfo.gpu:
            name = pkg_info["name"]["cpu"]
        else:
            if isinstance(pkg_info["name"]["gpu"], str):
                name = pkg_info["name"]["gpu"]
            else:
                if SysInfo.cuda == "8.0":
                    name = pkg_info["name"]["gpu"]["cuda80"]
                elif SysInfo.cuda == "9.0":
                    name = pkg_info["name"]["gpu"]["cuda90"]
                else:
                    name = pkg_info["name"]["gpu"]["other"]
    return (name, True)

def parse_pkg_version(pkg_info):
    version = ""
    logger.debug("version: {0}".format(pkg_info["version"]))
    if (pkg_info["version"] == None) or isinstance(pkg_info["version"], str):
        version = pkg_info["version"]
    else:
        if SysInfo.os == TOOLSFORAI_OS_WIN:
            if (pkg_info["version"] == None) or isinstance(pkg_info["version"]["win"], str):
                version = pkg_info["version"]["win"]
            else:
                if not SysInfo.gpu:
                    version = pkg_info["version"]["win"]["cpu"]
                else:
                    if (pkg_info["version"] == None) or isinstance(pkg_info["version"]["win"]["gpu"], str):
                        version = pkg_info["version"]["win"]["gpu"]
                    else:
                        if SysInfo.cuda == "8.0":
                            version = pkg_info["version"]["win"]["gpu"]["cuda80"]
                        elif SysInfo.cuda == "9.0":
                            version = pkg_info["version"]["win"]["gpu"]["cuda90"]
                        else:
                            version = pkg_info["version"]["win"]["gpu"]["other"]
        elif SysInfo.os == TOOLSFORAI_OS_LINUX:
            if (pkg_info["version"] == None) or isinstance(pkg_info["version"]["linux"], str):
                version = pkg_info["version"]["linux"]
            else:
                if not SysInfo.gpu:
                    version = pkg_info["version"]["linux"]["cpu"]
                else:
                    if (pkg_info["version"] == None) or isinstance(pkg_info["version"]["linux"]["gpu"], str):
                        version = pkg_info["version"]["linux"]["gpu"]
                    else:
                        if SysInfo.cuda == "8.0":
                            version = pkg_info["version"]["linux"]["gpu"]["cuda80"]
                        elif SysInfo.cuda == "9.0":
                            version = pkg_info["version"]["linux"]["gpu"]["cuda90"]
                        else:
                            version = pkg_info["version"]["linux"]["gpu"]["other"]
        elif SysInfo.os == TOOLSFORAI_OS_MACOS:
            return (None, False)
        else:
            logger.error("Fail to parse config.yaml to get version. Your OS can't support auto-installation.")
            return (None, False)
    return (version, True)

def parse_pkg_type(pkg_info):
    type = ""
    if isinstance(pkg_info["type"], str):
        type = pkg_info["type"]
    else:
        if SysInfo.os == TOOLSFORAI_OS_WIN:
            if isinstance(pkg_info["type"]["win"], str):
                type = pkg_info["type"]["win"]
            else:
                if not SysInfo.gpu:
                    type = pkg_info["type"]["win"]["cpu"]
                else:
                    if isinstance(pkg_info["type"]["win"]["gpu"], str):
                        type = pkg_info["type"]["win"]["gpu"]
                    else:
                        if SysInfo.cuda == "8.0":
                            type = pkg_info["type"]["win"]["gpu"]["cuda80"]
                        elif SysInfo.cuda == "9.0":
                            type = pkg_info["type"]["win"]["gpu"]["cuda90"]
                        else:
                            type = pkg_info["type"]["win"]["gpu"]["other"]
        elif SysInfo.os == TOOLSFORAI_OS_LINUX:
            if isinstance(pkg_info["type"]["linux"], str):
                type = pkg_info["type"]["linux"]
            else:
                if not SysInfo.gpu:
                    type = pkg_info["type"]["linux"]["cpu"]
                else:
                    if isinstance(pkg_info["type"]["linux"]["gpu"], str):
                        type = pkg_info["type"]["linux"]["gpu"]
                    else:
                        if SysInfo.cuda == "8.0":
                            type = pkg_info["type"]["linux"]["gpu"]["cuda80"]
                        elif SysInfo.cuda == "9.0":
                            type = pkg_info["type"]["linux"]["gpu"]["cuda90"]
                        else:
                            type = pkg_info["type"]["linux"]["gpu"]["other"]
        elif SysInfo.os == TOOLSFORAI_OS_MACOS:
            return (None, False)
        else:
            logger.error("Fail to parse config.yaml to get type. Your OS can't support auto-installation.")
            return (None, False)
    return (type, True)

def parse_pkg_pkg(pkg_info):
    pkg = ""
    if isinstance(pkg_info["pkg"], str):
        pkg = pkg_info["pkg"]
    else:
        if SysInfo.os == TOOLSFORAI_OS_WIN:
            if isinstance(pkg_info["pkg"]["win"], str):
                pkg = pkg_info["pkg"]["win"]
            else:
                if not SysInfo.gpu:
                    if isinstance(pkg_info["pkg"]["win"]["cpu"], str):
                        pkg = pkg_info["pkg"]["win"]["cpu"]
                    else:
                        if SysInfo.python == "35":
                            pkg = pkg_info["pkg"]["win"]["cpu"]["python35"]
                        elif SysInfo.python == "36":
                            pkg = pkg_info["pkg"]["win"]["cpu"]["python36"]
                        else:
                            logger.Error("Fail to parse config.yaml to get pkg, we only support python35 or python36, please make sure python version is appropriate.")
                            return (None, False)
                else:
                    if isinstance(pkg_info["pkg"]["win"]["gpu"], str):
                        pkg = pkg_info["pkg"]["win"]["gpu"]
                    else:
                        if SysInfo.python == "35":
                            if isinstance(pkg_info["pkg"]["win"]["gpu"]["python35"], str):
                                pkg = pkg_info["pkg"]["win"]["gpu"]["python35"]
                            else:
                                if SysInfo.cuda == "8.0":
                                    pkg = pkg_info["pkg"]["win"]["gpu"]["python35"]["cuda80"]
                                elif SysInfo.cuda == "9.0":
                                    pkg = pkg_info["pkg"]["win"]["gpu"]["python35"]["cuda90"]
                                else:
                                    pkg = pkg_info["pkg"]["win"]["gpu"]["python35"]["other"]
                        elif SysInfo.python == "36":
                            if isinstance(pkg_info["pkg"]["win"]["gpu"]["python36"], str):
                                pkg = pkg_info["pkg"]["win"]["gpu"]["python36"]
                            else:
                                if SysInfo.cuda == "8.0":
                                    pkg = pkg_info["pkg"]["win"]["gpu"]["python36"]["cuda80"]
                                elif SysInfo.cuda == "9.0":
                                    pkg = pkg_info["pkg"]["win"]["gpu"]["python36"]["cuda90"]
                                else:
                                    pkg = pkg_info["pkg"]["win"]["gpu"]["python36"]["other"]
                        else:
                            logger.Error("Fail to parse config.yaml to get pkg, we only support python35 or python36, please make sure python version is appropriate.")
                            return (None, False)
        elif SysInfo.os == TOOLSFORAI_OS_LINUX:
            if isinstance(pkg_info["pkg"]["linux"], str):
                pkg = pkg_info["pkg"]["linux"]
            else:
                if not SysInfo.gpu:
                    if isinstance(pkg_info["pkg"]["linux"]["cpu"], str):
                        pkg = pkg_info["pkg"]["linux"]["cpu"]
                    else:
                        if SysInfo.python == "35":
                            pkg = pkg_info["pkg"]["linux"]["cpu"]["python35"]
                        elif SysInfo.python == "36":
                            pkg = pkg_info["pkg"]["linux"]["cpu"]["python36"]
                        else:
                            logger.Error(
                                "Fail to parse config.yaml to get pkg, we only support python35 or python36, please make sure python version is appropriate.")
                            return (None, False)
                else:
                    if isinstance(pkg_info["pkg"]["linux"]["gpu"], str):
                        pkg = pkg_info["pkg"]["linux"]["gpu"]
                    else:
                        if SysInfo.python == "35":
                            if isinstance(pkg_info["pkg"]["linux"]["gpu"]["python35"], str):
                                pkg = pkg_info["pkg"]["linux"]["gpu"]["python35"]
                            else:
                                if SysInfo.cuda == "8.0":
                                    pkg = pkg_info["pkg"]["linux"]["gpu"]["python35"]["cuda80"]
                                elif SysInfo.cuda == "9.0":
                                    pkg = pkg_info["pkg"]["linux"]["gpu"]["python35"]["cuda90"]
                                else:
                                    pkg = pkg_info["pkg"]["linux"]["gpu"]["python35"]["other"]
                        elif SysInfo.python == "36":
                            if isinstance(pkg_info["pkg"]["linux"]["gpu"]["python36"], str):
                                pkg = pkg_info["pkg"]["win"]["gpu"]["python36"]
                            else:
                                if SysInfo.cuda == "8.0":
                                    pkg = pkg_info["pkg"]["linux"]["gpu"]["python36"]["cuda80"]
                                elif SysInfo.cuda == "9.0":
                                    pkg = pkg_info["pkg"]["linux"]["gpu"]["python36"]["cuda90"]
                                else:
                                    pkg = pkg_info["pkg"]["linux"]["gpu"]["python36"]["other"]
                        else:
                            logger.Error(
                                "Fail to parse config.yaml to get pkg, we only support python35 or python36, please make sure python version is appropriate.")
                            return (None, False)
        elif SysInfo.os == TOOLSFORAI_OS_MACOS:
            return (None, False)
        else:
            logger.error("Fail to parse config.yaml to get pkg. Your OS can't support auto-installation.")
            return (None, False)
    return (pkg, True)


def pip_software_install(pkg_info, options, user, verbose):
    pip_ops = []
    if options:
        pip_ops = options.split()
    elif user:
        pip_ops = ["--user"]
    if not verbose:
        pip_ops.append("-q")
    i = 0
    for pkg_item in pkg_info["pip"]:
        i = i + 1
        name, status1 = parse_pkg_name(pkg_item)
        logger.debug("i: {0}, name: {1}".format(i, name))
        version, status2 = parse_pkg_version(pkg_item)
        logger.debug("i: {0}, version: {1}".format(i, version))
        type, status3 = parse_pkg_type(pkg_item)
        logger.debug("i: {0}, name: {1}, version: {2}, type: {3}".format(i, name, version, type))
        if status1 and status2 and status3:
            if type == "0":
                logger.error("Your OS can't support auto-installation")
            elif type == "1":
                pip_install_package(name, pip_ops, version)
            elif type == "2":
                pkg, status4 = parse_pkg_pkg(pkg_item)
                if status4:
                    pip_install_package(name, pip_ops, version, pkg)
                else:
                    logger.error("Fail to parse config.yaml to get pkg.")
            elif type == "3":
                pip_uninstall_packge(name, pip_ops, version)
                pkg, status4 = parse_pkg_pkg(pkg_item)
                if status4:
                    pip_install_package(name, pip_ops, version, pkg)
                else:
                    logger.error("Fail to parse config.yaml to get pkg.")
        else:
            logger.error("Fail to parse config.yaml to get pkg.")