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
        ]