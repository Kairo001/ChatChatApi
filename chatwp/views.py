""" Vistas de la app de chat. """

#Django
from multiprocessing import context
from django.http import JsonResponse, HttpResponse
from django.views.generic import TemplateView, ListView, View
from django.utils import timezone

# Utilidades
import json
import requests
import base64
import magic

# Modelos
from chatwp.models import File, Message, Conversation

mime = magic.Magic(mime=True)

class RoomTemplateView(TemplateView):
    """ Vista del chat de la sala seleccionada. """

    template_name = "chatwp/room.html"

    def get_context_data(self, **kwargs):

        context = super(RoomTemplateView, self).get_context_data(**kwargs)
        conversations = Conversation.objects.all()
        context['conversations'] = conversations
        return context

class SendMessageView(View):
    """Vista para enviar mensajes de texto a 360Dialog."""

    def post(self, request, *args, **kwargs):
        post_data = json.loads(request.body.decode("utf-8"))

        url = "https://api.chat-api.com/instance231311/sendMessage?token=lapwv37y0sbtzzrp"

        chatId = post_data['chatId']
        
        payload = {
            "chatId": chatId,
            "body": post_data['message']
        }

        payload = json.dumps(payload)

        headers = {
            'Content-Type': "application/json",
        }

        response = requests.post(url, data=payload, headers=headers)
        status = int(response.status_code)
        response = response.json()
        if response['sent']:
            Message.objects.create(
                id = response['id']
            )
        response = json.dumps(response)
        return HttpResponse(response, content_type="application/json", status=status)

class SendMediaView(View):
    """Vista para enviar imágenes y texto a 360Dialog."""
    def post(self, request, *args, **kwargs):
        file = request.FILES.getlist('file')[0]
        caption = request.POST.get('caption')
        chat_id = request.POST.get('chatId') + '@c.us'

        file = File.objects.create(
            caption = caption,
            file=file
        )

        mime_data = mime.from_file(file.file.path)

        url = "https://api.chat-api.com/instance231311/sendFile?token=lapwv37y0sbtzzrp"

        headers = {
            'Content-Type': "application/json",
        }
        data = open(file.file.path, 'rb').read()
        data = base64.b64encode(data).decode('utf-8')
        new_data = f'data:{mime_data};base64,{data}'

        filename = file.file.name.split('/')[1]

        data = {
            'chatId': chat_id,
            'body': new_data,
            'filename': filename,
            'caption': caption
        }

        data = json.dumps(data)

        upload = requests.post(url,data=data,headers=headers)

        response = upload.json()

        response = json.dumps(response)
        
        return HttpResponse(response, content_type="application/json", status=int(upload.status_code))

class MessagesListView(ListView):
    """Vista para lograr el scroll infinito en el chat."""
    paginate_by = 6
 
    def get_queryset(self, *args, **kwargs):
        conversation = Conversation.objects.get(chat_id=self.kwargs['chat_id'])
        queryset = Message.objects.filter(conversation=conversation).order_by('-time')
        self.object_list = queryset
        return queryset
 
    def get(self, *args, **kwargs):
        response = {}
        response['success'] = True
        paginator = self.get_paginator(self.get_queryset(), self.paginate_by)
        num_pages = paginator.num_pages
        page = int(self.request.GET.get('page', 1))
        if page > num_pages:
            response['success'] = False
            return JsonResponse(response)

        response['page'] = page + 1
        context_data = super().get_context_data(**kwargs)
        message_list = context_data['object_list']
        print(message_list.count())
        message_json_list = []
        for message in message_list:
            message_json = {}
            message_json['id'] = message.id
            message_json['body'] = message.body
            message_json['created'] = message.get_time_message()
            message_json['from_me'] = message.from_me
            message_json['type_message'] = message.type_message
            message_json['caption'] = message.caption
            message_json['quoted_msg_body'] = message.quoted_msg_body
            message_json['quoted_msg_type'] = message.quoted_msg_type
            message_json['state'] = message.state
            message_json_list.append(message_json)
        response['messages'] = message_json_list
        return JsonResponse(response)

class UpdateChatView(View):
    """Vista para actualizar los mensajes no leidos de un chat a 0"""
    def post(self, request, *args, **kwargs):
        post_data = json.loads(request.body.decode("utf-8"))
        chat_id = post_data['chat_id']
        try:
            chat = Conversation.objects.get(chat_id=chat_id)
            chat.unread_msn = 0
            chat.save()
            return JsonResponse({'error':False})
        except:
            return JsonResponse({'error':True})