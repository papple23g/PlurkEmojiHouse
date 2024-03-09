# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.db import models
from taggit.managers import TaggableManager

#表符模組
class Emoji(models.Model):
    url=models.CharField(max_length=100)
    tags = TaggableManager()
    imagehash_str = models.TextField(blank=True,null=True)
    #定義獲取圖片hash數值
    def getImagehash(self):
        #若該數值已經被計算過，就直接從資料庫獲取數值
        if self.imagehash_str:
            imagehash_=imagehash.hex_to_hash(self.imagehash_str)
            return imagehash_
        #若該數值尚未被計算過，就進行計算並儲存該hash數據
        else:
            imagehash_=HashOfImage_inputUrl(self.url)
            Emoji.objects.filter(id=self.id).update(imagehash_str=str(imagehash_))
            return imagehash_
       
    def __unicode__(self):  # __str__ on Python 3
        return ','.join(self.tags.names())

#組合表符模組
class CombindEmoji(models.Model):
    combind_url=models.TextField() #組合表符網址，使用「|」作為斷行符號
    emoji_url_set = TaggableManager()
    def __unicode__(self):  # __str__ on Python 3
        return ','.join(self.emoji_url_set.names())


from PIL import Image # python -m pip install Pillow
import imagehash
from io import BytesIO
import requests as req
import certifi
#定義函數:輸入圖片網址計算hash數值
def HashOfImage_inputUrl(img_src):
    response = req.get(img_src, verify=certifi.where())
    image = Image.open(BytesIO(response.content))
    return imagehash.average_hash(image)