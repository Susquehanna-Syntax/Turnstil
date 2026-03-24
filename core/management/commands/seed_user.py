from django.core.management.base import BaseCommand
from core.models import User, Person

class Command(BaseCommand):
    help = 'Create a regular User through terminal'

    def add_arguments(self, parser):
        parser.add_argument('--username', type=str)
        parser.add_argument('--password', type=str)
        parser.add_argument('--email', type=str)
        parser.add_argument('--name', type=str)

    def handle(self, *args, **options):
        username = options.get('username')
        user, created  = User.objects.create_user(
            username=options['username'],

        defaults = {
            'email': options['email'],
            'role': 'attendee',
            'is_staff': False,
            'is_superuser': False,
        },
        )
        if not created:
            self.stdout.write(self.style.WARNING(f'User "{username}" already exists'))
            return
        user.set_password(options['password'])
        user.save()
        Person.objects.create(
            user=user,
            name=options['name'],
            email=options['email'],
            visibility={'email': True, 'organization': True, 'phone': False, 'links': True},
        )


        self.stdout.write(self.style.SUCCESS(
          f'Created user: {username} '
        ))

