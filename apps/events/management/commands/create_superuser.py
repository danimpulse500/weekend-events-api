from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = "Create a superuser if one doesn't exist"

    def handle(self, *args, **options):
        if not User.objects.filter(username='weekendeventsofficial').exists():
            User.objects.create_superuser(
                username='weekendeventsofficial',
                email='weekendeventsofficial@gmail.com',
                password='@ll4Jesus'
            )
            self.stdout.write(
                self.style.SUCCESS('✓ Superuser created successfully')
            )
        else:
            self.stdout.write('✓ Superuser already exists')
