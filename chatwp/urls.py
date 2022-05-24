""" Urls de la app de chat. """

#Django
from django.urls import path

# Vistas
from chatwp import views

urlpatterns = [
    path('room/<slug:slug>/', views.RoomTemplateView.as_view(), name="room"),
    path('send_message/', views.SendMessageView.as_view(), name='send_message'),
    path('send_media/', views.SendMediaView.as_view(), name="send_media"),
    path('messages/<chat_id>/', views.MessagesListView.as_view(), name='get_messages'),
    path('update_chat/', views.UpdateChatView.as_view(), name="update_chat")
]