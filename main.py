#coding=utf-8
from init import TOOLSFORAI_OS_LINUX, TOOLSFORAI_OS_WIN
from init import SysInfo
from init import logger, set_options
import utils
import install_pkg

import logging
import os
import _thread


def main():
    args, unknown = set_options()
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    if args.cuda80:
        SysInfo.cuda80 = True

    logger.info("Detecting system information ...")
    if not utils.detect_os() or not utils.detect_python_version() or not utils.detect_gpu():
        return
    utils.detect_git()
    if (SysInfo.os == TOOLSFORAI_OS_WIN):
        utils.detect_vs()
    if (SysInfo.gpu):
        if not utils.detect_cuda():
            return
        utils.detect_cudnn()

    target_dir = ''
    if SysInfo.os == TOOLSFORAI_OS_WIN:
        target_dir = os.path.sep.join([os.getenv("APPDATA"), "Microsoft", "ToolsForAI", "RuntimeSDK"])
    elif SysInfo.os == TOOLSFORAI_OS_LINUX:
        target_dir = os.path.sep.join([os.path.expanduser('~'), '.toolsforai', 'RuntimeSDK'])

    try:
        _thread.start_new_thread(install_pkg.install_cntk, (target_dir,))
    except:
        logger.error("Fail to startup install_cntk thread!")

    pkg_info = utils.rd_config()
    install_pkg.pip_software_install(pkg_info, args.options, args.user, args.verbose)
    utils.delete_env("AITOOLS_CNTK_ROOT")
    utils.fix_directory_ownership()
    for pkg in SysInfo.fail_install:
        logger.info("Fail to install {0}. Please try to run installer script again!".format(pkg))
    logger.info('Setup finishes.')
    input('Press enter to exit.')

if __name__ == "__main__":
    main()