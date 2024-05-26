from django.apps import AppConfig

class ProducerAppConfig(AppConfig):
    name = 'app'

    def ready(self):
        from app import assembling_message
        assembling_message()

