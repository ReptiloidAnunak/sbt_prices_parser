from django import forms
from .models import Supplier

class SupplierAdminForm(forms.ModelForm):
    class Meta:
        model = Supplier
        fields = "__all__"

    def clean_website(self):
        website = self.cleaned_data.get("website")

        if not website:
            return None

        website = str(website).strip()

        if website.lower() == "nan":
            return None

        if not website.startswith(("http://", "https://")):
            website = "https://" + website

        return website