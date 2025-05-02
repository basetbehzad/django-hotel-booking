from django import forms
from .models import Place  # Assuming you have a Place model


class PlaceSearchForm(forms.Form):
    CATEGORY_CHOICES = [("", "Any Category")] + Place.CATEGORY_CHOICES  # Add default choice

    name = forms.CharField(required=False, label="Hotel Name")
    category = forms.ChoiceField(choices=CATEGORY_CHOICES, required=False, label="Category")
    address = forms.CharField(required=False, label="Address")
    min_price = forms.DecimalField(required=False, min_value=0, label="Min Price")
    max_price = forms.DecimalField(required=False, min_value=0, label="Max Price")
    amenities = forms.MultipleChoiceField(
        choices=[("wifi", "WiFi"), ("parking", "Parking"), ("pool", "Pool")],
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Amenities"
    )
