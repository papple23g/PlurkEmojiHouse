# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin

from myapp.models import Emoji,CombindEmoji,SiteViews
admin.site.register(Emoji)
admin.site.register(CombindEmoji)


@admin.register(SiteViews)
class SiteViewsAdmin(admin.ModelAdmin):
    list_display = ("name", "total", "imported_total", "imported_at")
    readonly_fields = list_display

    def has_add_permission(self, request: object) -> bool:
        return False

    def has_delete_permission(self, request: object, obj: object = None) -> bool:
        return False

