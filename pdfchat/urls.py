from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views

app_name = 'pdfchat'

urlpatterns = [
    path('login', views.login_view, name="login_view"),
    path('register', views.register_view, name="register_view"),
    path('register_user', views.register, name="register"),
    path('', views.index, name="index"),
    path('ai', views.ai, name="ai"),
    path('cpa', views.cpa, name="cpa"),
    path('legal', views.legal, name="legal"),
    path('hr', views.hr, name="hr"),
    path('clients', views.clients, name="clients"),
    path('library', views.library, name="library"),
    path('upload', views.upload_view, name="upload_view"),
    path('upload_file', views.upload, name="upload"),
    path('prompts', views.prompts, name="prompts"),
    path('settings', views.settings, name="settings"),
    path('help', views.help, name="help"),
    path('contact', views.contact, name="contact"),
    path('signout', views.sign_out, name="sign_out"),
    path('get_percentage', views.get_percentage, name="get_percentage"),
    # history actions
    path('get_history', views.get_history, name='get_history'),
    path('create_history', views.create_history, name="create_history"),
    path('delete_history', views.delete_history, name="delete_history"),
    #
    path('chat', views.chat, name="chat"),
    path('get_chat', views.get_chat, name='get_chat'),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
