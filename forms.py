
import re
from django import forms
from .models import Student


class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = ["roll_number", "name", "branch"]

        widgets = {
            "roll_number": forms.TextInput(attrs={
                "placeholder": "Enter numbers only",
                "inputmode": "numeric",
                "pattern": "[0-9]+",
                "oninput": "this.value = this.value.replace(/[^0-9]/g, '')",
                "autocomplete": "off",
            }),
            "name": forms.TextInput(attrs={
                "placeholder": "Enter student name"
            }),
            "branch": forms.Select(choices=[
                ("", "Select Branch"),
                ("CSE", "CSE"),
                ("EE", "EE"),
                ("ECE", "ECE"),
                ("BIOTEC", "BIOTEC"),
                ("ME", "ME"),
            ]),
        }

    def clean_roll_number(self):
        roll_number = self.cleaned_data["roll_number"].strip()

        if not re.fullmatch(r"[0-9]+", roll_number):
            raise forms.ValidationError(
                "Roll number mein sirf 0 se 9 tak ke numbers allowed hain."
            )

        return roll_number
