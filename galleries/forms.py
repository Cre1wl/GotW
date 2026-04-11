from django import forms
from .models import Gallery, GalleryImage


class GalleryForm(forms.ModelForm):
    """Форма для создания/редактирования галереи"""

    class Meta:
        model = Gallery
        fields = ['name', 'description', 'is_public', 'max_images']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_public': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'max_images': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 200}),
        }


class GalleryImageForm(forms.ModelForm):
    """Форма для загрузки изображения"""

    class Meta:
        model = GalleryImage
        fields = ['image', 'title', 'description', 'alt_text', 'is_primary']
        widgets = {
            'image': forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'alt_text': forms.TextInput(attrs={'class': 'form-control'}),
            'is_primary': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean_image(self):
        image = self.cleaned_data.get('image')
        if image:
            if image.size > 10 * 1024 * 1024:
                raise forms.ValidationError('Файл слишком большой. Максимум 10MB')
        return image


# Простая форма для массовой загрузки без виджета с multiple
class MultipleImageUploadForm(forms.Form):
    """Форма для массовой загрузки изображений"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Создаем 5 полей для загрузки изображений
        for i in range(1, 6):
            self.fields[f'image_{i}'] = forms.ImageField(
                required=False,
                widget=forms.ClearableFileInput(attrs={
                    'class': 'form-control',
                    'accept': 'image/*'
                }),
                label=f'Изображение {i}'
            )

    def clean(self):
        cleaned_data = super().clean()
        images = []
        for i in range(1, 6):
            image = cleaned_data.get(f'image_{i}')
            if image:
                if image.size > 10 * 1024 * 1024:
                    raise forms.ValidationError(f'Файл {image.name} слишком большой. Максимум 10MB')
                images.append(image)

        if not images:
            raise forms.ValidationError('Выберите хотя бы одно изображение')

        cleaned_data['images'] = images
        return cleaned_data