#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import os.path
import sys

logger = logging.getLogger('Card_generator')
logger.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(levelname)s  %(lineno)d  %(message)s')


sh_info = logging.StreamHandler(stream=sys.stdout)
sh_info.setLevel(logging.INFO)
sh_info.setFormatter(formatter)

# will be caught by anki and displayed in a
# pop-up window
sh_error = logging.StreamHandler(stream=sys.stderr)
sh_error.setLevel(logging.ERROR)
sh_error.setFormatter(formatter)

addon_dir = os.path.dirname(__file__)
log_path = os.path.join(addon_dir, 'CardGen_log.log')
fh = logging.FileHandler(log_path, mode="w", encoding='utf-8')
fh.setLevel(logging.DEBUG)
fh.setFormatter(formatter)

logger.addHandler(fh)
logger.addHandler(sh_error)
logger.addHandler(sh_info)


#logger.warning("Verbose Log will be saved at {}".format(
   # os.path.abspath(log_path)))