from django import forms
from .models import World


class WorldForm(forms.ModelForm):
    """Форма для создания/редактирования мира"""

    class Meta:
        model = World
        fields = ['name', 'description', 'cover_image', 'theme_color']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Название мира'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Опишите ваш мир...'
            }),
            'cover_image': forms.FileInput(attrs={
                'class': 'form-control'
            }),
            'theme_color': forms.TextInput(attrs={
                'class': 'form-control',
                'type': 'color',
                'style': 'width: 100px;'
            }),
        }

    def clean_name(self):
        name = self.cleaned_data.get('name')
        if len(name) < 3:
            raise forms.ValidationError('Название мира должно содержать минимум 3 символа')
        return name


class WorldSettingsForm(forms.ModelForm):
    """Форма настроек мира"""

    class Meta:
        model = World
        fields = ['name', 'description', 'cover_image', 'theme_color', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'cover_image': forms.FileInput(attrs={'class': 'form-control'}),
            'theme_color': forms.TextInput(attrs={'class': 'form-control', 'type': 'color'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }