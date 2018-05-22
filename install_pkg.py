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

def pip_install_cntk(pkg_info, options):
    if not ((SysInfo.os == TOOLSFORAI_OS_WIN) or (SysInfo.os == TOOLSFORAI_OS_LINUX)):
        logger.info("CNTK(Python) can not be supported on your OS, we recommend 64-bit Windows-10 OS or 64-bit Linux OS.")
        return
    if SysInfo.gpu:
        name = pkg_info["cntk"]["name"]["gpu"]
        if SysInfo.cuda == "8.0":
            version = pkg_info["cntk"]["cuda80"]
            wheel_ver = SysInfo.python
            arch = "win_amd64" if SysInfo.os == TOOLSFORAI_OS_WIN else "linux_x86_64"
            gpu_type = "GPU" if SysInfo.gpu else "CPU-Only"
            pkg = "https://cntk.ai/PythonWheel/{0}/cntk-{1}-cp{2}-cp{2}m-{3}.whl".format(gpu_type, version, wheel_ver, arch)
            return pip_install_package(name, options, version, pkg)
        elif SysInfo.cuda == "9.0":
            version = pkg_info["cntk"]["version"]["cuda90"]
            return pip_install_package(name, options, version)
    else:
        name = pkg_info["cntk"]["name"]["cpu"]
        version = pkg_info["cntk"]["version"]["cpu"]
        return pip_install_package(name, options, version)

def pip_install_scipy(pkg_info, options):
    logger.info("Begin to install scipy(numpy, scipy) ...")
    name = pkg_info["scipy"]["numpy"]["name"]
    version = pkg_info["scipy"]["numpy"]["version"]
    if not pip_install_package(name, options, version):
        logger.error("Pip_install_scipy terminated due to numpy installation failure.")
        return False

    name = pkg_info["scipy"]["scipy"]["name"]
    version = pkg_info["scipy"]["scipy"]["version"]
    if not pip_install_package(name, options, version):
        logger.error("Pip_install_scipy terminated due to scipy installation failure.")
        return False
    return True

def pip_install_tensorflow(pkg_info, options):
    if SysInfo.gpu:
        name = pkg_info["tensorflow"]["name"]["gpu"]
        if SysInfo.cuda == "8.0":
            if SysInfo.os == TOOLSFORAI_OS_WIN:
                version = pkg_info["tensorflow"]["version"]["cuda80"]["win"]
            elif SysInfo.os == TOOLSFORAI_OS_LINUX:
                version = pkg_info["tensorflow"]["version"]["cuda80"]["linux"]
        else:
            version = pkg_info["tensorflow"]["version"]["cuda90"]
    else:
        name = pkg_info["tensorflow"]["name"]["cpu"]
        version = pkg_info["tensorflow"]["version"]["cpu"]
    return pip_install_package(name, options, version)

def pip_install_pytorch(pkg_info, options):
    name = pkg_info["pytorch"]["torch"]["name"]
    version = pkg_info["pytorch"]["torch"]["version"]
    if SysInfo.os == TOOLSFORAI_OS_MACOS:
        pip_install_package(name, options, version)
    elif SysInfo.os == TOOLSFORAI_OS_WIN or SysInfo.os == TOOLSFORAI_OS_LINUX:
        wheel_ver = SysInfo.python
        arch = "win_amd64" if SysInfo.os == TOOLSFORAI_OS_WIN else "linux_x86_64"
        if not SysInfo.gpu:
            gpu_type = "cpu"
        else:
            gpu_type = "cu80" if SysInfo.cuda == "8.0" else "cu90"
        pkg = "http://download.pytorch.org/whl/{0}/{1}-{2}-cp{3}-cp{3}m-{4}.whl".format(gpu_type, name, version, wheel_ver, arch)
        pip_install_package(name, options, version, pkg)
    else:
        logger.error("Fail to install pytorch.")
        logger.warning("Pytorch installation can not be supported on your OS! We recommand 64-bit Windows-10, Linux and Macos.")

    name = pkg_info["pytorch"]["torchvision"]["name"]
    version = pkg_info["pytorch"]["torchvision"]["version"]
    pip_install_package(name, options, version)

def pip_install_keras(pkg_info, options):
    name = pkg_info["Keras"]["name"]
    version = pkg_info["Keras"]["version"]
    return pip_install_package(name, options, version)

def pip_install_caffe2(pkg_info, options):
    if not (SysInfo.os == TOOLSFORAI_OS_WIN):
        logger.warning("Fail to install caffe2. In non-Windows OS, you should manually install caffe2 from source.")
        return
    name = pkg_info["caffe2"]["name"]
    version = pkg_info["caffe2"]["version"]
    arch = "win_amd64"
    wheel_ver = SysInfo.python
    if SysInfo.gpu and SysInfo.cuda == "8.0":
        pkg = "https://raw.githubusercontent.com/linmajia/ai-package/master/caffe2/{0}/caffe2_gpu-{0}-cp{1}-cp{1}m-{2}.whl".format(
            version, wheel_ver, arch)
    else:
        pkg = "https://raw.githubusercontent.com/linmajia/ai-package/master/caffe2/{0}/caffe2-{0}-cp{1}-cp{1}m-{2}.whl".format(
            version, wheel_ver, arch)
    return pip_install_package(name, options, version, pkg)

def pip_install_theano(pkg_info, options):
    name = pkg_info["Theano"]["name"]
    version = pkg_info["Theano"]["version"]
    return pip_install_package(name, options, version)

def pip_install_mxnet(pkg_info, options):
    version = pkg_info["mxnet"]["version"]
    if SysInfo.gpu:
        if SysInfo.cuda == "8.0":
            name = pkg_info["mxnet"]["name"]["gpu"]["cuda80"]
        else:
            name = pkg_info["mxnet"]["name"]["gpu"]["cuda90"]
    else:
        name =  pkg_info["mxnet"]["name"]["cpu"]

    return pip_install_package(name, options, version)

def pip_install_chainer(pkg_info, options):
    # cupy installation for GPU linux
    logger.info("Begin to install chainer(cupy, chainer, chainermn) ...")
    version = pkg_info["chainer"]["cupy"]["version"]
    if (SysInfo.gpu and (SysInfo.os == TOOLSFORAI_OS_LINUX)):
        if SysInfo.cuda == "8.0":
            name = pkg_info["chainer"]["cupy"]["name"]["linux"]["cuda80"]
        elif SysInfo.cuda == "9.0":
            name = pkg_info["chainer"]["cupy"]["name"]["linux"]["cuda90"]
        else:
            name = pkg_info["chainer"]["cupy"]["name"]["linux"]["other"]
        pip_install_package(name, options)
    elif (SysInfo.gpu and (SysInfo.os == TOOLSFORAI_OS_WIN)):
        try:
            name = pkg_info["chainer"]["cupy"]["name"]["win"]
            cupy = importlib.import_module(name)
            if (not utils._version_compare(version, cupy.__version__)):
                logger.warning("Cupy's version is too low, please manually upgrade cupy >= 2.0.0.")
            else:
                logger.info("cupy is already installed.")
        except ImportError:
            logger.warning("On windows, please manully install cupy. You can reference this link https://github.com/Microsoft/vs-tools-for-ai/blob/master/docs/prepare-localmachine.md#chainer.")

    name = pkg_info["chainer"]["chainer"]["name"]
    version = pkg_info["chainer"]["chainer"]["version"]
    pip_install_package(name, options, version)

    name = pkg_info["chainer"]["chainermn"]["name"]
    version = pkg_info["chainer"]["chainermn"]["version"]
    if not pip_install_package(name, options, version):
        logger.warning("On Linux, in order to install chainermn, please first manually install libmpich-dev and then run installer script again.")

def pip_install_converter(pkg_info, options):
    logger.info("Begin to install converter(coremltools, onnx, tf2onnx, onnxmltools and winmltools) ...")
    try:
        #1 coremltools
        name = pkg_info["converter"]["coremltools"]["name"]
        version = pkg_info["converter"]["coremltools"]["version"]
        if SysInfo.os == TOOLSFORAI_OS_WIN:
            if SysInfo.git:
                pkg = "git+https://github.com/apple/coremltools@v0.8"
                pip_install_package(name, options, version, pkg)
            else:
                SysInfo.fail_install.append("%s %s" % (name, version))
                logger.warning("Fail to install {0}. Please manually install git and run installer script again.".format(name))
        else:
            pip_install_package(name, options, version)

        #2 onnx
        name = pkg_info["converter"]["onnx"]["name"]
        version = pkg_info["converter"]["onnx"]["version"]
        pip_install_package(name, options, version)

        #3 tf2onnx
        name = pkg_info["converter"]["tf2onnx"]["name"]
        version = pkg_info["converter"]["tf2onnx"]["version"]
        if not SysInfo.git:
            utils.fail_install.append("%s %s" % (name, version))
            logger.warning("Fail to install {0}. Please manually install git and run installer script again.".format(name))
        else:
            pkg = "git+https://github.com/onnx/tensorflow-onnx.git@r0.1"
            if utils.module_exists(name):
                logger.info("{0} is already installed. We will uninstall it and upgrade to the latest version.".format(name))
                pip_uninstall_packge(name, options, version)
            pip_install_package(name, options, version, pkg)

        #4 onnxmltools
        name = pkg_info["converter"]["onnxmltools"]["name"]
        version = pkg_info["converter"]["onnxmltools"]["version"]
        if utils.module_exists(name):
            logger.info("{0} is already installed.".format(name))
        else:
            pip_install_package(name, options, version)

        #5 winmltools
        name = pkg_info["converter"]["winmltools"]["name"]
        version = pkg_info["converter"]["winmltools"]["version"]
        if utils.module_exists(name):
            logger.info("{0} is already installed.".format(name))
        else:
            pip_install_package(name, options, version)
    except Exception as e:
        logger.error("Fail to install converter, unexpected error! Please run installer again!")

def pip_install_ml_software(pkg_info, options):
    logger.info("Begin to install ml software(scikit-learn, xgboost and libsvm) ...")

    #1 scikit-learn
    name = pkg_info["ml_software"]["scikit-learn"]["name"]
    version = pkg_info["ml_software"]["scikit-learn"]["version"]
    pip_install_package(name, options, version)

    #2 xgboost
    name = pkg_info["ml_software"]["xgboost"]["name"]
    version = pkg_info["ml_software"]["xgboost"]["version"]
    if SysInfo.os != TOOLSFORAI_OS_WIN:
        if not pip_install_package(name, options, version):
            logger.warning("In order to install xgboost, C++ compiler is needed.")
    else:
        wheel_ver = SysInfo.python
        arch = "win_amd64"
        pkg = "https://raw.githubusercontent.com/linmajia/ai-package/master/xgboost/{0}/xgboost-{0}-cp{1}-cp{1}m-{2}.whl".format(version, wheel_ver, arch)
        pip_install_package(name, options, version, pkg)

    #3 libsvm
    name = pkg_info["ml_software"]["libsvm"]["name"]
    version = pkg_info["ml_software"]["libsvm"]["version"]
    if SysInfo.os != TOOLSFORAI_OS_WIN:
        logger.warning(
            "Fail to install libsvm. On Linux or Mac, in order to install {0}=={1}, please manually download source code and install it.".format(
                name, version))
    else:
        wheel_ver = SysInfo.python
        arch = "win_amd64"
        pkg = "https://raw.githubusercontent.com/linmajia/ai-package/master/libsvm/{0}/libsvm-{0}-cp{1}-cp{1}m-{2}.whl".format(version, wheel_ver, arch)
        logger.debug("Pip install libsvm from {0}".format(pkg))
        pip_install_package(name, options, version, pkg)

def pip_install_extra_software(pkg_info, options):
    logger.info("Begin to install extra software(jupyter, matplotlib, and pandas) ...")

    #1 jupyter
    name = pkg_info["extra_software"]["jupyter"]["name"]
    version = pkg_info["extra_software"]["jupyter"]["version"]
    if utils.module_exists(name):
        logger.info("{0} is already installed.".format(name))
    else:
        pip_install_package(name, options, version)

    #2 matplotlib
    name = pkg_info["extra_software"]["matplotlib"]["name"]
    version = pkg_info["extra_software"]["matplotlib"]["version"]
    if utils.module_exists(name):
        logger.info("{0} is already installed.".format(name))
    else:
        pip_install_package(name, options, version)

    #3 pandas
    name = pkg_info["extra_software"]["pandas"]["name"]
    version = pkg_info["extra_software"]["pandas"]["version"]
    if utils.module_exists(name):
        logger.info("{0} is already installed.".format(name))
    else:
        pip_install_package(name, options, version)

def pip_software_install(pkg_info, options, user, verbose):
    pip_ops = []
    if options:
        pip_ops = options.split()
    elif user:
        pip_ops = ["--user"]
    if not verbose:
        pip_ops.append("-q")
    if not pip_install_scipy(pkg_info, pip_ops):
        return
    pip_install_cntk(pkg_info, pip_ops)
    pip_install_tensorflow(pkg_info, pip_ops)
    pip_install_pytorch(pkg_info, pip_ops)
    pip_install_mxnet(pkg_info, pip_ops)
    pip_install_chainer(pkg_info, pip_ops)
    pip_install_theano(pkg_info, pip_ops)
    pip_install_keras(pkg_info, pip_ops)
    pip_install_caffe2(pkg_info, pip_ops)
    pip_install_ml_software(pkg_info, pip_ops)
    pip_install_converter(pkg_info, pip_ops)
    pip_install_extra_software(pkg_info, pip_ops)