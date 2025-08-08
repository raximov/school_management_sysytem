from django import forms
from .models import Student

class StudentRegisterForm(forms.ModelForm):
    username = forms.CharField(max_length=150)
    password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = Student
        exclude = ['user']  # user will be set in the view

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Render as select fields
        self.fields['gender'].widget = forms.Select(choices=Student.GENDER_CHOICES)
        self.fields['nationality'].widget = forms.Select(choices=Student._meta.get_field('nationality').choices)
        self.fields['citizenship'].widget = forms.Select(choices=[
            ('uzbekiston', "O'zbekiston"),
            ('rossiya', 'Rossiya'),
            ('qozogiston', "Qozog'iston"),
            ('tojikiston', 'Tojikiston'),
            ('qirgiziston', "Qirg'iziston"),
            ('turkmaniston', 'Turkmaniston'),
            ('boshqa', 'Boshqa'),
        ])
        self.fields['country'].widget = forms.Select(choices=Student._meta.get_field('country').choices)

        # Initially, region and district are empty
        self.fields['region'].widget = forms.Select(choices=Student.REGION_CHOICES)
        self.fields['district'].widget = forms.Select(choices=Student.DISTRICT_CHOICES)

        # Dynamically set region choices based on country
        if 'country' in self.data:
            country = self.data.get('country')
            if country == 'uzbekiston':
                self.fields['region'].widget = forms.Select(choices=Student.REGION_CHOICES)
            # Add more country-region logic if needed

        # Dynamically set district choices based on region
        if 'region' in self.data:
            region = self.data.get('region')
            districts = getattr(Student, 'DISTRICT_CHOICES', {}).get(region, [])
            self.fields['district'].widget = forms.Select(choices=[('', '---------')] + districts)