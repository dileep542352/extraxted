#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# (c) ACE 

import os

class Config(object):
    # get a token from @BotFather
    BOT_TOKEN = os.environ.get("BOT_TOKEN", "6216840269:AAFNzApyRlXuZ94T3UZgd-XqNun2mA40kJU")
    API_ID = int(os.environ.get("API_ID", "7856100"))
    API_HASH = os.environ.get("API_HASH", "dba409d7e8d44ab5bb689378deea1792")
    AUTH_USERS = "1411895712"

