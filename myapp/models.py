# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.db import models
from taggit.managers import TaggableManager

#表符模組
class Emoji(models.Model):
    url=models.CharField(max_length=100)
    tags = TaggableManager()
    def __unicode__(self):  # __str__ on Python 3
        return ','.join(self.tags.names())

#組合表符模組
class CombindEmoji(models.Model):
    combind_url=models.TextField() #組合表符網址，使用「|」作為斷行符號
    emoji_url_set = TaggableManager()
    def __unicode__(self):  # __str__ on Python 3
        return ','.join(self.emoji_url_set.names())