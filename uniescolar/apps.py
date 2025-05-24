from django.apps import AppConfig

import os



class UniescolarConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'uniescolar'

    def ready(self):
        from django.contrib.auth import get_user_model
        User = get_user_model()

        if os.environ.get('CREATE_SUPERUSER') == 'True':
            if not User.objects.filter(username='admin').exists():
                User.objects.create_superuser(
                    username='admin',
                    email='',
                    password='universo2025'
                )
                print("Superusuário criado automaticamente.")
