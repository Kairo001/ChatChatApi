import os

# Channels
from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter

# Django
from django.urls import path, re_path
from django.core.asgi import get_asgi_application

# Enrutamiento
from chatwp import consumers as consumers_chatwp

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

application = ProtocolTypeRouter({
    "http": URLRouter([
        re_path(r"^webhook/$", consumers_chatwp.WebHookConsumer.as_asgi()),
        re_path(r"", get_asgi_application()),
    ]),
    "websocket": AuthMiddlewareStack(
        URLRouter([
            path('ws/<str:room_name>/', consumers_chatwp.ChatConsumer.as_asgi()),
        ])
    ),
})
