# -*- coding: utf-8 -*-
# EverJudge
# @author: Ayanami_404<jiyizhuo2011@hotmail.com>
# @maintainer: Project EverJudge
# @license: GPL3
# @version: 0.1.0
# Copyright Project EverJudge 2025, All Rights Reserved.

from .api import *

import everjudge_share
import logging

_logger = logging.getLogger("EverJudge Application")


def set_main_application(app_: Application) -> None: # It's originally in the api.py, but we do not want it to be widely used.
    everjudge_share.app = app_
    return

if __name__ == '__main__':
    _logger.info("Starting EverJudge Application...")
    set_main_application(create_application(__name__, host="0.0.0.0", port=8080, debug=True))
    set_plugin_manager(create_plugin_manager())
    get_plugin_manager().load_plugins()
    get_main_application().mainloop()
