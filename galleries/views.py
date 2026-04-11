from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.contenttypes.models import ContentType
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator
from django.views.decorators.http import require_POST
from .models import Gallery, GalleryImage
from .forms import GalleryForm, GalleryImageForm, MultipleImageUploadForm


@login_required
def gallery_list(request, content_type_id, object_id):
    """Список галерей для объекта"""
    content_type = get_object_or_404(ContentType, id=content_type_id)
    obj = content_type.get_object_for_this_type(id=object_id)

    # Проверка прав (только владелец может видеть галереи)
    if hasattr(obj, 'creator') and obj.creator != request.user and not request.user.is_superuser:
        messages.error(request, 'У вас нет доступа к этой галерее')
        return redirect('worlds:library')

    galleries = Gallery.objects.filter(content_type=content_type, object_id=object_id)

    return render(request, 'galleries/gallery_list.html', {
        'galleries': galleries,
        'obj': obj,
        'content_type_id': content_type_id,
        'object_id': object_id,
    })


@login_required
def gallery_create(request, content_type_id, object_id):
    """Создание новой галереи"""
    content_type = get_object_or_404(ContentType, id=content_type_id)
    obj = content_type.get_object_for_this_type(id=object_id)

    # Проверка прав
    if hasattr(obj, 'creator') and obj.creator != request.user and not request.user.is_superuser:
        messages.error(request, 'У вас нет прав для создания галереи')
        return redirect('worlds:library')

    if request.method == 'POST':
        form = GalleryForm(request.POST)
        if form.is_valid():
            gallery = form.save(commit=False)
            gallery.content_type = content_type
            gallery.object_id = object_id
            gallery.created_by = request.user
            gallery.save()
            messages.success(request, f'Галерея "{gallery.name}" успешно создана!')
            return redirect('galleries:gallery_detail', gallery_id=gallery.id)
    else:
        form = GalleryForm()

    return render(request, 'galleries/gallery_form.html', {
        'form': form,
        'obj': obj,
        'title': 'Создание галереи',
    })


@login_required
def gallery_detail(request, gallery_id):
    """Просмотр галереи"""
    gallery = get_object_or_404(Gallery, id=gallery_id)
    obj = gallery.content_object

    # Проверка прав
    if hasattr(obj, 'creator') and obj.creator != request.user and not request.user.is_superuser:
        messages.error(request, 'У вас нет доступа к этой галерее')
        return redirect('worlds:library')

    images = gallery.images.all()

    # Пагинация изображений
    paginator = Paginator(images, 20)
    page_number = request.GET.get('page')
    images_page = paginator.get_page(page_number)

    return render(request, 'galleries/gallery_detail.html', {
        'gallery': gallery,
        'images': images_page,
        'obj': obj,
    })


@login_required
def gallery_edit(request, gallery_id):
    """Редактирование галереи"""
    gallery = get_object_or_404(Gallery, id=gallery_id)
    obj = gallery.content_object

    # Проверка прав
    if hasattr(obj, 'creator') and obj.creator != request.user and not request.user.is_superuser:
        messages.error(request, 'У вас нет прав для редактирования')
        return redirect('worlds:library')

    if request.method == 'POST':
        form = GalleryForm(request.POST, instance=gallery)
        if form.is_valid():
            form.save()
            messages.success(request, f'Галерея "{gallery.name}" обновлена!')
            return redirect('galleries:gallery_detail', gallery_id=gallery.id)
    else:
        form = GalleryForm(instance=gallery)

    return render(request, 'galleries/gallery_form.html', {
        'form': form,
        'gallery': gallery,
        'obj': obj,
        'title': 'Редактирование галереи',
    })


@login_required
def gallery_delete(request, gallery_id):
    """Удаление галереи"""
    gallery = get_object_or_404(Gallery, id=gallery_id)
    obj = gallery.content_object

    # Проверка прав
    if hasattr(obj, 'creator') and obj.creator != request.user and not request.user.is_superuser:
        messages.error(request, 'У вас нет прав для удаления')
        return redirect('worlds:library')

    if request.method == 'POST':
        gallery_name = gallery.name
        gallery.delete()
        messages.success(request, f'Галерея "{gallery_name}" удалена!')

        # Перенаправление обратно
        content_type_id = ContentType.objects.get_for_model(obj).id
        return redirect('galleries:gallery_list', content_type_id=content_type_id, object_id=obj.id)

    return render(request, 'galleries/gallery_confirm_delete.html', {'gallery': gallery})


@login_required
def image_upload(request, gallery_id):
    """Загрузка изображения в галерею"""
    gallery = get_object_or_404(Gallery, id=gallery_id)
    obj = gallery.content_object

    # Проверка прав
    if hasattr(obj, 'creator') and obj.creator != request.user and not request.user.is_superuser:
        return JsonResponse({'error': 'Нет прав'}, status=403)

    if request.method == 'POST':
        form = GalleryImageForm(request.POST, request.FILES)
        if form.is_valid():
            image = form.save(commit=False)
            image.gallery = gallery
            image.uploaded_by = request.user
            image.save()

            messages.success(request, 'Изображение успешно загружено!')

            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'image_id': image.id,
                    'image_url': image.image.url,
                    'title': image.title,
                })

            return redirect('galleries:gallery_detail', gallery_id=gallery.id)
    else:
        form = GalleryImageForm()

    return render(request, 'galleries/image_upload.html', {
        'form': form,
        'gallery': gallery,
    })


@login_required
def multiple_image_upload(request, gallery_id):
    """Массовая загрузка изображений"""
    gallery = get_object_or_404(Gallery, id=gallery_id)
    obj = gallery.content_object

    if hasattr(obj, 'creator') and obj.creator != request.user and not request.user.is_superuser:
        messages.error(request, 'У вас нет прав')
        return redirect('worlds:library')

    if request.method == 'POST':
        form = MultipleImageUploadForm(request.POST, request.FILES)
        if form.is_valid():
            images = form.cleaned_data['images']
            uploaded_count = 0

            for image_file in images:
                if gallery.can_add_image():
                    GalleryImage.objects.create(
                        gallery=gallery,
                        image=image_file,
                        uploaded_by=request.user,
                        title=f"Изображение {image_file.name}"
                    )
                    uploaded_count += 1
                else:
                    messages.warning(request, f'Достигнут лимит изображений в галерее')
                    break

            if uploaded_count > 0:
                messages.success(request, f'Загружено {uploaded_count} изображений!')
            return redirect('galleries:gallery_detail', gallery_id=gallery.id)
    else:
        form = MultipleImageUploadForm()

    return render(request, 'galleries/multiple_upload.html', {
        'form': form,
        'gallery': gallery,
    })


@login_required
def image_edit(request, image_id):
    """Редактирование изображения"""
    image = get_object_or_404(GalleryImage, id=image_id)
    gallery = image.gallery
    obj = gallery.content_object

    if hasattr(obj, 'creator') and obj.creator != request.user and not request.user.is_superuser:
        messages.error(request, 'У вас нет прав')
        return redirect('worlds:library')

    if request.method == 'POST':
        form = GalleryImageForm(request.POST, instance=image)
        if form.is_valid():
            form.save()
            messages.success(request, 'Изображение обновлено!')
            return redirect('galleries:gallery_detail', gallery_id=gallery.id)
    else:
        form = GalleryImageForm(instance=image)

    return render(request, 'galleries/image_edit.html', {
        'form': form,
        'image': image,
        'gallery': gallery,
    })


@login_required
@require_POST
def image_delete(request, image_id):
    """Удаление изображения"""
    image = get_object_or_404(GalleryImage, id=image_id)
    gallery = image.gallery
    obj = gallery.content_object

    if hasattr(obj, 'creator') and obj.creator != request.user and not request.user.is_superuser:
        return JsonResponse({'error': 'Нет прав'}, status=403)

    image.delete()
    messages.success(request, 'Изображение удалено!')

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True})

    return redirect('galleries:gallery_detail', gallery_id=gallery.id)


@login_required
@require_POST
def set_primary_image(request, image_id):
    """Установка основного изображения"""
    image = get_object_or_404(GalleryImage, id=image_id)
    gallery = image.gallery
    obj = gallery.content_object

    if hasattr(obj, 'creator') and obj.creator != request.user and not request.user.is_superuser:
        return JsonResponse({'error': 'Нет прав'}, status=403)

    # Снимаем флаг со всех изображений галереи
    gallery.images.update(is_primary=False)
    # Устанавливаем новое основное
    image.is_primary = True
    image.save()

    messages.success(request, 'Основное изображение обновлено!')

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True})

    return redirect('galleries:gallery_detail', gallery_id=gallery.id)