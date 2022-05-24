""" Consumers de Channels.
Los consumers son una abstracción que le permite crear aplicaciones ASGI fácilmente.
Los consumers hacen un par de cosas en particular:
* Estructura el código como una serie de funciones que se llamarán cada vez que ocurra un
evento, en lugar de hacer que escriba un ciclo de enventos.
* Permite escribir código asíncoro o síncrono y se ocupa de tranferencias y subprocesos.

Cuando Channels acepta una conexión WebSocket, consulta la configuración de enrutamiento raíz
para buscar un consumidor y luego llama a varias funciones en el consumidor para manejar eventos
de la conexión.
"""

# Utilidades
import json
from datetime import timedelta, datetime
import time
from tracemalloc import start

# # Channels
from channels.generic.http import AsyncHttpConsumer
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async

# Modelos
from chatwp.models import Client, Conversation, Message

class WebHookConsumer(AsyncHttpConsumer):
    """
    Consumer del webhook
    Este consumidor recibe las notificaciones del webhook de chat-api y las procesa por medio de una petición http 
    para así poder devolver un código de estado.
    """

    async def handle(self, body):
        body = json.loads(body)
        start = time.time()
        print(body)
        messages = None
        ack = None
        chat_update = None

        try:
            messages = body['messages'][0]
        except:
            try:
                ack = body['ack'][0]
            except:
                chat_update = body['chatUpdate'][0]
        
        channel_name = await self.find_channel_name()

        print(channel_name)

        if messages:
            print("Mensaje actualizado")
            await self.save_message(messages)
            print("Mensaje actualizado")
            await self.channel_layer.send(channel_name, {
                "type": "chat.message",
                "notification_type": "messages",
                "data": body,
            })
        if ack:
            print("Mensaje actualizado por ack")
            await self.update_state_message(ack)
            print("Mensaje actualizado por ack")
            await self.channel_layer.send(channel_name, {
                "type": "chat.message",
                "notification_type": "ack",
                "data": body,
            })
        if chat_update:
            print("Conversation actualizado")
            await self.update_chat(chat_update)
            print("Conversation actualizado")
            await self.channel_layer.send(channel_name, {
                "type": "chat.message",
                "notification_type": "chat_update",
                "data": body,
            })

        message = {'message':"Received notification"}
        message = json.dumps(message).encode('utf-8')
        print(time.time() - start)
        await self.send_response(200, message, headers=[
            (b"Content-Type", b"text/plain"),
        ])

    @database_sync_to_async    
    def save_message(self, messages):
        """Método para guardar un mensaje."""
        conversation = Conversation.objects.filter(chat_id=messages["chatId"])[0]
        if messages["type"] == "chat":
            if len(messages["body"]) > 45:
                conversation.last_msn = messages["body"][0:45] + "..."
            else:
                conversation.last_msn = messages["body"] 
        elif messages["type"] == "image":
            conversation.last_msn = "Foto"
        elif messages["type"] == "ptt":
            conversation.last_msn = "Audio"
        elif messages["type"] == "location":
            conversation.last_msn = "Ubicación"
        else: 
            conversation.last_msn = "Otro"

        conversation.time = messages["time"]
        if not messages["fromMe"]:
            conversation.unread_msn += 1

        conversation.save()

        print(conversation)

        try:
            message = Message.objects.get(id=messages["id"])
        except:
            message = Message.objects.create(id=messages['id'])

        message.body = messages["body"]
        message.from_me = messages["fromMe"]
        message.author = messages["author"]
        message.time = messages["time"]
        message.conversation = conversation
        message.type_message = messages["type"]
        message.sender_name = messages["senderName"]
        message.caption = messages["caption"]
        message.quoted_msg_body = messages["quotedMsgBody"]
        message.quoted_msg_type = messages["quotedMsgType"],
        message.state = 3 if messages["fromMe"]==False else 0
        message.save()

    @database_sync_to_async    
    def update_state_message(self, ack):
        """Método para actualizar el estado de un mensaje."""
        state = 0
        if ack["status"] == "sent":
            state = 1
        elif ack["status"] == "delivered":
            state = 2
        elif ack["status"] == "viewed":
            state = 3

        message = Message.objects.get(pk=ack["id"])
        message.state = state
        message.save()
    
    @database_sync_to_async
    def update_chat(self, chat_update):
        """Método para crear o actualizar un dialogo."""
        if chat_update['new']:
            if not Conversation.objects.filter(chat_id=chat_update['new']['id']).exists():
                print("Chat no existe!")
                conversation = Conversation.objects.create(
                    chat_id = chat_update['new']['id'],
                    chat_name = chat_update['new']['name']
                )

    @database_sync_to_async
    def find_channel_name(self):
        """Método para encontra el nombre del canal al cual pertenece la conversación."""
        try:
            return Client.objects.all()[0].channel_name
        except:
            return "dsdasdasdas1231231312312"
    

class ChatConsumer(AsyncWebsocketConsumer):
    """ Consumer de chat.
    Cuando un usuario publica un mensaje, una función de JavaScript transmitirá el mensaje a través de WebSocket a un ChatConsumer,
    este recibirá ese mensaje y lo reenviará al grupo conrrespondiente al nombre de la sala. Cada ChatCosumer en el mismo grupo (y,
    por lo tanto, en la misma sala) recibirá el mensaje del grupo y lo reenviará a través de WebSocket a JavaScript, donde se agre_
    gará al registro de chat.

    Cada consumer tiene un alcanse que contiene información sobre su conexión, incluidos, en particular, los argumentos posicionales
    o de palabras clave de la ruta URL y el usuario autenticado actualmente, si lo hay. 
    """

    async def connect(self):
        await self.create_client()
        await self.accept()

    async def disconnect(self, close_code):
        await self.delete_client()

    async def receive(self, text_data):
        data =json.loads(text_data)
        message = data['message']
        numeroId = data['numeroId']
        room = data['room']

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type' : 'chat_message',
                'message' : message,
                'numeroId' : numeroId,
                'room' : room,
            }
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'notification_type': event['notification_type'],
            'data': event['data']
        }))

    @database_sync_to_async
    def create_client(self):
        Client.objects.create(channel_name=self.channel_name)

    @database_sync_to_async
    def delete_client(self):
        Client.objects.filter(channel_name=self.channel_name).delete()