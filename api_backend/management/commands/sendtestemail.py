from django.core.management.base import BaseCommand
from django.conf import settings
from django.core.mail import send_mail

class Command(BaseCommand):
    help = 'Send a test email'

    def handle(self, *args, **options):
        send_mail(
            subject='Test Email',
            message='Это тестовое письмо, отправленное через management command.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=['dishonored787898@gmail.com'], # замените на нужный email
            fail_silently=False,
        )
        self.stdout.write(self.style.SUCCESS("Письмо успешно отправлено!"))
