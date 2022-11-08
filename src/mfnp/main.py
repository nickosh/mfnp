# Mainframe Notepad

# Copyright © 2022 Nikolay Shishov. All rights reserved.
# SPDX-License-Identifier: MIT

import logging
import sys

from dearpygui import core
from dearpygui.demo import show_demo

from mfnp import config, ui
from mfnp.logger import LoggerHandler

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

if __name__ == "__main__":
    core.start_dearpygui()
