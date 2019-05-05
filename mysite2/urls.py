"""mysite2 URL Configuration

The `urlpatterns` list routes URLs to  For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url
from django.contrib import admin
from myapp.views import *

from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^home$',home),
    url(r'^PlurkEmojiHouse$',PlurkEmojiHouse),
    url(r'^PlurkEmojiHouse/$',PlurkEmojiHouse),
    url(r'^PlurkEmojiHouse/search_by_tag',search_by_tag),
    url(r'^PlurkEmojiHouse/search_by_url',search_by_url),
    url(r'^PlurkEmojiHouse/search_by_uuu',search_by_url_list),
    url(r'^PlurkEmojiHouse/emoji_add_tag',emoji_add_tag),
    url(r'^PlurkEmojiHouse/delete_tag',delete_tag),
    url(r'^PlurkEmojiHouse/search_tags',search_tags),
    url(r'^PlurkEmojiHouse/PlurkUrlHtml',PlurkUrlHtml),
    url(r'^PlurkEmojiHouse/NumOfEmoji_and_NumOfTag',NumOfEmoji_and_NumOfTag),
    url(r'^PlurkEmojiHouse/numOfEmojiPageBtn',numOfEmojiPageBtn),
    url(r'^PlurkEmojiHouse/test',test),
    url(r'^PlurkEmojiHouse/emoji_list_add_tag',emoji_list_add_tag),
    
    
]+ static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

#for testing
urlpatterns.extend([
    url(r'^testHttpResponse$',testHttpResponse),
    url(r'^testRender$',testRender),
    url(r'^testBrython$',testBrython)
    ])
