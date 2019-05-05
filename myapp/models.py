# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.db import models
from taggit.managers import TaggableManager

class Emoji(models.Model):
    url=models.CharField(max_length=100)
    tags = TaggableManager()
    def __unicode__(self):  # __str__ on Python 3
        return ','.join(self.tags.names())
