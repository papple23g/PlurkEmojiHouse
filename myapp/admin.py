# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin

from myapp.models import Emoji,CombindEmoji
admin.site.register(Emoji)
admin.site.register(CombindEmoji)

