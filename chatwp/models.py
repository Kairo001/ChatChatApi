"""Modelos de la app de chat de whatsapp"""

# Django
from django.db import models
from django.utils import timezone

# Utilidades
from datetime import datetime

class File(models.Model):
    """Modelo para guardar los archivos de los chat."""
    caption = models.CharField(max_length=128, null=True)
    file = models.FileField(upload_to="files/")
    created = models.DateTimeField(
        'Creado en',
        auto_now_add=True,
        help_text='Fecha y hora en la cual el objeto fue creado.'
    )

    def __str__(self):
        return "Archivo creado el {}.".format(self.created.strftime('%Y-%m-%d %H:%M'))

class Client(models.Model):
    """Modelo para guardar las conexiones a los canales."""
    channel_name = models.CharField('Nombre del canal', primary_key=True, max_length=80)

    created = models.DateTimeField(
        'create at',
        auto_now_add=True,
        help_text='Fecha y hora en la cual el objeto fue creado.'
    )

    modified = models.DateTimeField(
        'modified at',
        auto_now=True,
        help_text='Fecha y hora de la última modificación del objeto.'
    )

    class Meta:
        """ Opciones Meta. """
        get_latest_by = 'created'
        ordering = ['-created', '-modified']


class Conversation(models.Model):
    """Modelo para pintar las conversaciones actualues de un usuario."""
    chat_id = models.CharField('Id del chat', primary_key=True, max_length=20, editable=False)
    unread_msn = models.PositiveSmallIntegerField(help_text='Número de mensajes no leidos.', default=0)
    last_msn = models.CharField(max_length=50, blank=True, null=True)
    chat_name = models.CharField(max_length=20)
    time = models.PositiveIntegerField(help_text="timestamp", blank=True, null=True)

    created = models.DateTimeField(
        'create at',
        auto_now_add=True,
        help_text='Fecha y hora en la cual el objeto fue creado.'
    )

    modified = models.DateTimeField(
        'modified at',
        auto_now=True,
        help_text='Fecha y hora de la última modificación del objeto.'
    )

    class Meta:
        """ Opciones Meta. """
        get_latest_by = 'created'
        ordering = ['-modified', '-created']


    def get_time_last_message(self):
        """Obtener la fecha del último mensaje."""
        time = datetime.fromtimestamp(self.time)
        now = timezone.now()

        date_time = time.date()
        date_now = now.date()

        if date_time == date_now:
            return time.strftime("%H:%M")

        elif (date_now - date_time).days == 1:
            return "Ayer"
        
        return time.strftime("%d/%m/%y")

class Message(models.Model):
    """Modelo para guardar los mensajes."""
    id = models.CharField('Id del mensaje', max_length=50, primary_key=True, editable=False)
    body = models.TextField(max_length=4096, blank=True, null=True)
    from_me = models.BooleanField(blank=True, null=True)
    author = models.CharField(max_length=20, blank=True, null=True)
    time = models.PositiveIntegerField(help_text="timestamp", blank=True, null=True)
    conversation = models.ForeignKey(Conversation, on_delete=models.PROTECT, related_name='messages', blank=True, null=True)
    type_message = models.CharField('Tipo de mensaje', max_length=16, blank=True, null=True)
    sender_name = models.CharField(max_length=64, blank=True, null=True, help_text="Nombre de quien envía el mensaje.")
    caption = models.CharField(max_length=128, help_text="Subtítulo de un mensaje cuando es de galería.", blank=True, null=True)
    quoted_msg_body = models.CharField(max_length=128, help_text="Cuerpo del mensaje al cual se está respondiendo", blank=True, null=True)
    quoted_msg_type = models.CharField(max_length=16, help_text="Tipo de mensaje al cual se está respondiendo.", blank=True, null=True)
    state = models.PositiveSmallIntegerField(default=0, help_text="Estado del mensaje: 1-Enviado, 2-Entregado, 3-Leido", blank=True, null=True)

    created = models.DateTimeField(
        'create at',
        auto_now_add=True,
        help_text='Fecha y hora en la cual el objeto fue creado.'
    )

    modified = models.DateTimeField(
        'modified at',
        auto_now=True,
        help_text='Fecha y hora de la última modificación del objeto.'
    )

    class Meta:
        """ Opciones Meta. """
        get_latest_by = 'created'
        ordering = ['-created', 'modified']

    def __str__(self):
        return "Mensaje {}".format(self.id)

    def get_time_message(self):
        """Obtener la fecha del mensaje."""
        time = datetime.fromtimestamp(self.time)
        return time.strftime("%H:%M")