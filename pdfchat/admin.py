from django.contrib import admin
from .models import Document, Activity, ChatHistory, Chat
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from pdfchat.models import Client

class ClientsInline(admin.StackedInline):
    model = Client
    can_delete = False
    verbose_name_plural = 'client'


class UserAdmin(BaseUserAdmin):
    inlines = [ClientsInline]

admin.site.unregister(User)
admin.site.register(User, UserAdmin)
# Register your models here.
admin.site.register(Document)
admin.site.register(Activity)
admin.site.register(ChatHistory)
admin.site.register(Chat)