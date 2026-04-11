from django import forms
from .models import Element, ElementType


class ElementTypeForm(forms.ModelForm):
    """Форма для создания/редактирования типа элемента"""

    class Meta:
        model = ElementType
        fields = ['name', 'description', 'icon', 'color', 'fields_schema']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'icon': forms.TextInput(attrs={'class': 'form-control'}),
            'color': forms.TextInput(attrs={'class': 'form-control', 'type': 'color'}),
            'fields_schema': forms.Textarea(
                attrs={'class': 'form-control', 'rows': 10, 'style': 'font-family: monospace;'}),
        }

    def clean_fields_schema(self):
        """Валидация JSON схемы"""
        import json
        data = self.cleaned_data['fields_schema']

        if isinstance(data, str):
            try:
                data = json.loads(data)
            except json.JSONDecodeError:
                raise forms.ValidationError("Неверный JSON формат")

        if not isinstance(data, dict):
            raise forms.ValidationError("Схема полей должна быть объектом JSON")

        return data


class DynamicElementForm(forms.Form):
    """Динамическая форма для создания/редактирования элемента"""

    def __init__(self, element_type, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.element_type = element_type

        for field_name, field_config in element_type.fields_schema.items():
            label = field_config.get('label', field_name)
            required = field_config.get('required', False)
            field_type = field_config.get('type', 'text')
            default = field_config.get('default', None)

            # Создаем поле в зависимости от типа
            if field_type == 'text':
                self.fields[field_name] = forms.CharField(
                    label=label,
                    required=required,
                    initial=default,
                    widget=forms.TextInput(attrs={
                        'class': 'form-control',
                        'placeholder': field_config.get('placeholder', '')
                    })
                )

            elif field_type == 'textarea':
                self.fields[field_name] = forms.CharField(
                    label=label,
                    required=required,
                    initial=default,
                    widget=forms.Textarea(attrs={
                        'class': 'form-control',
                        'rows': field_config.get('rows', 4),
                        'placeholder': field_config.get('placeholder', '')
                    })
                )

            elif field_type == 'number':
                self.fields[field_name] = forms.IntegerField(
                    label=label,
                    required=required,
                    initial=default,
                    min_value=field_config.get('min', None),
                    max_value=field_config.get('max', None),
                    widget=forms.NumberInput(attrs={
                        'class': 'form-control',
                        'min': field_config.get('min', ''),
                        'max': field_config.get('max', '')
                    })
                )

            elif field_type == 'boolean':
                self.fields[field_name] = forms.BooleanField(
                    label=label,
                    required=False,
                    initial=default if default is not None else False,
                    widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
                )

            elif field_type == 'date':
                self.fields[field_name] = forms.DateField(
                    label=label,
                    required=required,
                    initial=default,
                    widget=forms.DateInput(attrs={
                        'type': 'date',
                        'class': 'form-control'
                    })
                )

            elif field_type == 'datetime':
                self.fields[field_name] = forms.DateTimeField(
                    label=label,
                    required=required,
                    initial=default,
                    widget=forms.DateTimeInput(attrs={
                        'type': 'datetime-local',
                        'class': 'form-control'
                    })
                )

            elif field_type == 'time':
                self.fields[field_name] = forms.TimeField(
                    label=label,
                    required=required,
                    initial=default,
                    widget=forms.TimeInput(attrs={
                        'type': 'time',
                        'class': 'form-control'
                    })
                )

            elif field_type == 'color':
                self.fields[field_name] = forms.CharField(
                    label=label,
                    required=required,
                    initial=default or '#000000',
                    widget=forms.TextInput(attrs={
                        'type': 'color',
                        'class': 'form-control form-control-color',
                        'style': 'width: 100px;'
                    })
                )

            elif field_type == 'select':
                choices = field_config.get('choices', [])
                choice_list = [(c, c) for c in choices]
                self.fields[field_name] = forms.ChoiceField(
                    label=label,
                    required=required,
                    choices=choice_list,
                    initial=default,
                    widget=forms.Select(attrs={'class': 'form-select'})
                )

            elif field_type == 'multiselect':
                choices = field_config.get('choices', [])
                choice_list = [(c, c) for c in choices]
                self.fields[field_name] = forms.MultipleChoiceField(
                    label=label,
                    required=required,
                    choices=choice_list,
                    initial=default,
                    widget=forms.SelectMultiple(attrs={'class': 'form-select', 'size': 5})
                )

            elif field_type == 'url':
                self.fields[field_name] = forms.URLField(
                    label=label,
                    required=required,
                    initial=default,
                    widget=forms.URLInput(attrs={'class': 'form-control'})
                )

            elif field_type == 'email':
                self.fields[field_name] = forms.EmailField(
                    label=label,
                    required=required,
                    initial=default,
                    widget=forms.EmailInput(attrs={'class': 'form-control'})
                )

            elif field_type == 'phone':
                self.fields[field_name] = forms.CharField(
                    label=label,
                    required=required,
                    initial=default,
                    widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+7 (999) 123-45-67'})
                )

            elif field_type in ['image', 'file']:
                self.fields[field_name] = forms.ImageField(
                    label=label,
                    required=required,
                    widget=forms.FileInput(attrs={'class': 'form-control'})
                )

    def save(self, element=None):
        """Сохраняет данные в элемент"""
        if element is None:
            element = Element()

        element.data = {}
        for field_name in self.element_type.fields_schema.keys():
            if field_name in self.cleaned_data:
                value = self.cleaned_data[field_name]
                # Обработка особых типов
                if isinstance(value, bool):
                    element.data[field_name] = value
                elif hasattr(value, 'url'):  # File/Image field
                    element.data[field_name] = value.url
                else:
                    element.data[field_name] = value

        return element