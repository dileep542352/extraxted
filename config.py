#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# (c) ACE 

import os

class Config(object):
    # get a token from @BotFather
    BOT_TOKEN = os.environ.get("BOT_TOKEN", "6239183711:AAFjNSTd4AoLKBTrvTPRqQ1MbYZlNBjRyQU")
    API_ID = int(os.environ.get("API_ID", "7273627"))
    API_HASH = os.environ.get("API_HASH", "ee9172964fda7050eed58701c7ff8917")
    AUTH_USERS = "1833865556"

