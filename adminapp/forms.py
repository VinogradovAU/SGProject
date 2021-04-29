from django import forms


class BanTimeForm(forms.Form):
    ban_time = forms.CharField(required=False, label='', max_length=20,
                               widget=forms.NumberInput(attrs={'placeholder': 'на сколько дней', 'type': 'number'}))


