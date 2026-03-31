from django.forms import ModelForm
from .models import Event

class EventForm(ModelForm):
    class Meta:
        model = Event
        fields = [
            'name',
            'description',
            'location',
            'start_time',
            'end_time',
            'reg_open',
            'reg_close',
            'capacity',
<<<<<<< HEAD
        ]
=======
            'external_link',
        ]
>>>>>>> 6489d758485c56fa294002f439ead7fee94f3161
