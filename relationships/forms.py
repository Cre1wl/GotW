from django import forms
from .models import Relationship, RelationshipType


class RelationshipTypeForm(forms.ModelForm):
    """Форма для создания/редактирования типа связи"""

    class Meta:
        model = RelationshipType
        fields = ['name', 'reverse_name', 'description', 'color', 'icon', 'is_bidirectional', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'reverse_name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'color': forms.TextInput(attrs={'class': 'form-control', 'type': 'color'}),
            'icon': forms.TextInput(attrs={'class': 'form-control'}),
            'is_bidirectional': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class RelationshipForm(forms.ModelForm):
    """Форма для создания/редактирования связи"""

    class Meta:
        model = Relationship
        fields = ['relationship_type', 'to_element', 'description', 'strength', 'attributes']
        widgets = {
            'relationship_type': forms.Select(attrs={'class': 'form-select'}),
            'to_element': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'strength': forms.Select(attrs={'class': 'form-select'}),
            'attributes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'JSON формат'}),
        }

    def __init__(self, *args, **kwargs):
        self.world = kwargs.pop('world', None)
        self.from_element = kwargs.pop('from_element', None)
        super().__init__(*args, **kwargs)

        if self.world:
            # Фильтруем типы связей по миру (через элементы)
            self.fields['relationship_type'].queryset = RelationshipType.objects.filter(
                relationships__from_element__world=self.world
            ).distinct()

            # Фильтруем элементы для выбора
            self.fields['to_element'].queryset = self.world.elements.all()

            if self.from_element:
                self.fields['to_element'].queryset = self.world.elements.exclude(id=self.from_element.id)

    def clean_attributes(self):
        data = self.cleaned_data.get('attributes')
        if isinstance(data, str) and data:
            import json
            try:
                return json.loads(data)
            except json.JSONDecodeError:
                raise forms.ValidationError("Неверный JSON формат")
        return data or {}