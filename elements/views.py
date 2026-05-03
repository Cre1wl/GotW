import time
import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from .models import ElementType, Element
from worlds.models import World


@login_required
def category_create_ajax(request, world_id):
    """Создание категории через AJAX"""
    if request.method == 'POST':
        world = get_object_or_404(World, id=world_id, creator=request.user)
        name = request.POST.get('name')
        icon = request.POST.get('icon', 'cube')

        if name:
            if ElementType.objects.filter(name=name, world=world).exists():
                return JsonResponse({'error': f'Категория "{name}" уже существует в этом мире!'}, status=400)

            category = ElementType.objects.create(
                name=name,
                world=world,
                icon=icon
            )
            return JsonResponse({
                'id': category.id,
                'name': category.name,
                'icon': category.icon,
                'success': True
            })
        else:
            return JsonResponse({'error': 'Введите название категории'}, status=400)

    return JsonResponse({'error': 'Invalid request'}, status=400)


@login_required
def category_update(request, category_id):
    """Обновление категории"""
    category = get_object_or_404(ElementType, id=category_id, world__creator=request.user)

    if request.method == 'POST':
        name = request.POST.get('name')
        icon = request.POST.get('icon', 'cube')

        if name:
            if ElementType.objects.filter(name=name, world=category.world).exclude(id=category_id).exists():
                return JsonResponse({'error': f'Категория "{name}" уже существует!'}, status=400)
            category.name = name
            category.icon = icon
            category.save()
            return JsonResponse({'success': True, 'name': category.name, 'icon': category.icon})
        else:
            return JsonResponse({'error': 'Введите название категории'}, status=400)

    return JsonResponse({'error': 'Invalid request'}, status=400)


@login_required
def category_delete(request, category_id):
    """Удаление категории"""
    category = get_object_or_404(ElementType, id=category_id, world__creator=request.user)
    world_id = category.world.id

    if request.method == 'POST':
        category_name = category.name
        category.delete()
        messages.success(request, f'Категория "{category_name}" удалена!')
        return redirect('worlds:world_detail', world_id=world_id)

    return redirect('worlds:world_detail', world_id=world_id)


@login_required
def element_create(request, world_id):
    """Создание элемента с богатым набором полей"""
    world = get_object_or_404(World, id=world_id, creator=request.user)
    categories = world.element_types.all()

    if request.method == 'POST':
        name = request.POST.get('name')
        category_id = request.POST.get('category')

        if not name:
            messages.error(request, 'Введите название элемента')
            return redirect('elements:element_create', world_id=world.id)

        if not category_id:
            messages.error(request, 'Выберите категорию')
            return redirect('elements:element_create', world_id=world.id)

        category = get_object_or_404(ElementType, id=category_id, world=world)

        fields_schema = {}
        data = {}

        # Обработка обложки
        if 'cover_image' in request.FILES:
            uploaded_file = request.FILES['cover_image']
            timestamp = int(time.time())
            ext = uploaded_file.name.split('.')[-1].lower()
            filename = f'element_cover_{world.id}_{timestamp}.{ext}'
            file_path = default_storage.save(
                f'element_covers/{world.id}/{filename}',
                ContentFile(uploaded_file.read())
            )
            data['_cover'] = default_storage.url(file_path)

        # Получаем динамические поля
        field_indices = request.POST.getlist('field_index[]')

        for idx in field_indices:
            field_name = request.POST.get(f'field_name_{idx}')
            field_type = request.POST.get(f'field_type_{idx}')

            if field_name and field_name.strip():
                field_key = field_name.strip().lower().replace(' ', '_')

                fields_schema[field_key] = {
                    'name': field_name,
                    'type': field_type
                }

                value = None

                if field_type == 'checkbox':
                    value = request.POST.get(f'field_value_{idx}') == 'on'

                elif field_type == 'image' and request.FILES.get(f'field_file_{idx}'):
                    uploaded_file = request.FILES.get(f'field_file_{idx}')
                    timestamp = int(time.time())
                    ext = uploaded_file.name.split('.')[-1].lower()
                    filename = f'element_img_{world.id}_{timestamp}_{field_key}.{ext}'
                    file_path = default_storage.save(
                        f'element_images/{world.id}/{filename}',
                        ContentFile(uploaded_file.read())
                    )
                    value = default_storage.url(file_path)

                elif field_type == 'image_with_caption':
                    value = {}
                    if request.FILES.get(f'field_file_{idx}'):
                        uploaded_file = request.FILES.get(f'field_file_{idx}')
                        timestamp = int(time.time())
                        ext = uploaded_file.name.split('.')[-1].lower()
                        filename = f'element_img_{world.id}_{timestamp}_{field_key}.{ext}'
                        file_path = default_storage.save(
                            f'element_images/{world.id}/{filename}',
                            ContentFile(uploaded_file.read())
                        )
                        value['image'] = default_storage.url(file_path)
                    value['caption'] = request.POST.get(f'field_caption_{idx}', '')

                elif field_type == 'gallery':
                    value = []
                    for key in request.FILES:
                        if key.startswith(f'field_gallery_{idx}_'):
                            uploaded_file = request.FILES[key]
                            timestamp = int(time.time())
                            ext = uploaded_file.name.split('.')[-1].lower()
                            filename = f'element_gallery_{world.id}_{timestamp}_{field_key}_{key}.{ext}'
                            file_path = default_storage.save(
                                f'element_gallery/{world.id}/{filename}',
                                ContentFile(uploaded_file.read())
                            )
                            value.append(default_storage.url(file_path))

                elif field_type == 'select':
                    options = request.POST.get(f'field_options_{idx}', '')
                    fields_schema[field_key]['options'] = [opt.strip() for opt in options.split(',') if opt.strip()]
                    value = request.POST.get(f'field_value_{idx}', '')

                elif field_type == 'multiselect':
                    options = request.POST.get(f'field_options_{idx}', '')
                    fields_schema[field_key]['options'] = [opt.strip() for opt in options.split(',') if opt.strip()]
                    value = request.POST.getlist(f'field_value_{idx}[]')

                elif field_type == 'range':
                    range_config = request.POST.get(f'field_range_config_{idx}', '0,100')
                    parts = range_config.split(',')
                    fields_schema[field_key]['min'] = int(parts[0]) if len(parts) > 0 else 0
                    fields_schema[field_key]['max'] = int(parts[1]) if len(parts) > 1 else 100
                    value = int(request.POST.get(f'field_value_{idx}', 0))

                elif field_type == 'rating':
                    value = int(request.POST.get(f'field_value_{idx}', 0))

                elif field_type == 'tags':
                    tags = request.POST.get(f'field_value_{idx}', '')
                    value = [tag.strip() for tag in tags.split(',') if tag.strip()]

                elif field_type == 'file' and request.FILES.get(f'field_file_{idx}'):
                    uploaded_file = request.FILES.get(f'field_file_{idx}')
                    timestamp = int(time.time())
                    filename = f'element_file_{world.id}_{timestamp}_{field_key}_{uploaded_file.name}'
                    file_path = default_storage.save(
                        f'element_files/{world.id}/{filename}',
                        ContentFile(uploaded_file.read())
                    )
                    value = default_storage.url(file_path)

                else:
                    value = request.POST.get(f'field_value_{idx}', '')

                if value or (field_type == 'checkbox' and value is not None):
                    data[field_key] = value

        # Очистка пустых полей
        fields_schema = {k: v for k, v in fields_schema.items() if v.get('name') and v['name'].strip()}
        data = {k: v for k, v in data.items() if k in fields_schema or k == '_cover'}

        # Создаём элемент
        element = Element.objects.create(
            world=world,
            element_type=category,
            name=name,
            fields_schema=fields_schema,
            data=data
        )

        messages.success(request, f'Элемент "{name}" создан!')

        from .crm_integration import create_crm_contact
        create_crm_contact(element)

        return redirect('elements:element_detail', world_id=world.id, element_id=element.id)

    return render(request, 'elements/element_create.html', {
        'world': world,
        'categories': categories,
    })


@login_required
def element_detail(request, world_id, element_id):
    """Просмотр элемента"""
    world = get_object_or_404(World, id=world_id, creator=request.user)
    element = get_object_or_404(Element, id=element_id, world=world)

    # Преобразуем data в словарь, если это строка JSON
    if isinstance(element.data, str):
        try:
            element.data = json.loads(element.data)
        except:
            element.data = {}

    if isinstance(element.fields_schema, str):
        try:
            element.fields_schema = json.loads(element.fields_schema)
        except:
            element.fields_schema = {}

    return render(request, 'elements/element_detail.html', {
        'world': world,
        'element': element,
    })


@login_required
def element_edit(request, world_id, element_id):
    """Редактирование элемента с возможностью добавления новых полей"""
    world = get_object_or_404(World, id=world_id, creator=request.user)
    element = get_object_or_404(Element, id=element_id, world=world)

    # Преобразуем data в словарь, если это строка JSON
    if isinstance(element.data, str):
        try:
            element.data = json.loads(element.data)
        except:
            element.data = {}

    if isinstance(element.fields_schema, str):
        try:
            element.fields_schema = json.loads(element.fields_schema)
        except:
            element.fields_schema = {}

    if request.method == 'POST':
        # Проверяем, не является ли это запросом на удаление поля
        if 'delete_field' in request.POST:
            field_to_delete = request.POST.get('delete_field')
            if field_to_delete in element.fields_schema:
                del element.fields_schema[field_to_delete]
                if field_to_delete in element.data:
                    del element.data[field_to_delete]
                element.save()
                messages.success(request, f'Поле успешно удалено!')
                return redirect('elements:element_edit', world_id=world.id, element_id=element.id)
            else:
                messages.error(request, 'Поле не найдено')
                return redirect('elements:element_edit', world_id=world.id, element_id=element.id)

        # Обычное обновление элемента
        element.name = request.POST.get('name')

        # Обновляем обложку
        if 'cover_image' in request.FILES:
            uploaded_file = request.FILES['cover_image']
            timestamp = int(time.time())
            ext = uploaded_file.name.split('.')[-1].lower()
            filename = f'element_cover_{world.id}_{timestamp}.{ext}'
            file_path = default_storage.save(
                f'element_covers/{world.id}/{filename}',
                ContentFile(uploaded_file.read())
            )
            element.data['_cover'] = default_storage.url(file_path)

        # Копируем существующие схемы и данные
        fields_schema = element.fields_schema.copy() if element.fields_schema else {}
        data = element.data.copy() if element.data else {}

        # Обновляем существующие поля
        for field_key, field_config in fields_schema.items():
            field_type = field_config.get('type', 'text')

            if field_type == 'checkbox':
                value = request.POST.get(f'field_{field_key}') == 'on'
                data[field_key] = value

            elif field_type == 'image' and request.FILES.get(f'field_file_{field_key}'):
                uploaded_file = request.FILES.get(f'field_file_{field_key}')
                timestamp = int(time.time())
                ext = uploaded_file.name.split('.')[-1].lower()
                filename = f'element_img_{world.id}_{timestamp}_{field_key}.{ext}'
                file_path = default_storage.save(
                    f'element_images/{world.id}/{filename}',
                    ContentFile(uploaded_file.read())
                )
                data[field_key] = default_storage.url(file_path)

            elif field_type == 'image_with_caption':
                if field_key not in data:
                    data[field_key] = {}
                if request.FILES.get(f'field_file_{field_key}'):
                    uploaded_file = request.FILES.get(f'field_file_{field_key}')
                    timestamp = int(time.time())
                    ext = uploaded_file.name.split('.')[-1].lower()
                    filename = f'element_img_{world.id}_{timestamp}_{field_key}.{ext}'
                    file_path = default_storage.save(
                        f'element_images/{world.id}/{filename}',
                        ContentFile(uploaded_file.read())
                    )
                    data[field_key]['image'] = default_storage.url(file_path)
                caption = request.POST.get(f'field_caption_{field_key}', '')
                if caption:
                    data[field_key]['caption'] = caption

            elif field_type == 'gallery':
                if field_key not in data:
                    data[field_key] = []
                for key in request.FILES:
                    if key.startswith(f'field_gallery_{field_key}_'):
                        uploaded_file = request.FILES[key]
                        timestamp = int(time.time())
                        ext = uploaded_file.name.split('.')[-1].lower()
                        filename = f'element_gallery_{world.id}_{timestamp}_{field_key}_{key}.{ext}'
                        file_path = default_storage.save(
                            f'element_gallery/{world.id}/{filename}',
                            ContentFile(uploaded_file.read())
                        )
                        data[field_key].append(default_storage.url(file_path))

            elif field_type == 'tags':
                tags = request.POST.get(f'field_{field_key}', '')
                if tags:
                    data[field_key] = [tag.strip() for tag in tags.split(',') if tag.strip()]

            elif field_type == 'multiselect':
                values = request.POST.getlist(f'field_{field_key}[]')
                if values:
                    data[field_key] = values

            elif field_type == 'rating':
                value = request.POST.get(f'field_{field_key}', '0')
                if value:
                    data[field_key] = int(value)

            elif field_type == 'range':
                value = request.POST.get(f'field_{field_key}', '0')
                if value:
                    data[field_key] = int(value)

            elif field_type == 'file' and request.FILES.get(f'field_file_{field_key}'):
                uploaded_file = request.FILES.get(f'field_file_{field_key}')
                timestamp = int(time.time())
                filename = f'element_file_{world.id}_{timestamp}_{field_key}_{uploaded_file.name}'
                file_path = default_storage.save(
                    f'element_files/{world.id}/{filename}',
                    ContentFile(uploaded_file.read())
                )
                data[field_key] = default_storage.url(file_path)

            else:
                value = request.POST.get(f'field_{field_key}', '')
                if value:
                    data[field_key] = value

        # Добавляем новые поля
        new_field_indices = request.POST.getlist('new_field_index[]')

        for idx in new_field_indices:
            field_name = request.POST.get(f'new_field_name_{idx}')
            field_type = request.POST.get(f'new_field_type_{idx}')

            if field_name and field_name.strip():
                field_key = field_name.strip().lower().replace(' ', '_')

                fields_schema[field_key] = {
                    'name': field_name,
                    'type': field_type
                }

                if field_type == 'checkbox':
                    value = request.POST.get(f'new_field_value_{idx}') == 'on'
                    if value:
                        data[field_key] = value

                elif field_type == 'image' and request.FILES.get(f'new_field_file_{idx}'):
                    uploaded_file = request.FILES.get(f'new_field_file_{idx}')
                    timestamp = int(time.time())
                    ext = uploaded_file.name.split('.')[-1].lower()
                    filename = f'element_img_{world.id}_{timestamp}_{field_key}.{ext}'
                    file_path = default_storage.save(
                        f'element_images/{world.id}/{filename}',
                        ContentFile(uploaded_file.read())
                    )
                    data[field_key] = default_storage.url(file_path)

                elif field_type == 'image_with_caption':
                    value = {}
                    if request.FILES.get(f'new_field_file_{idx}'):
                        uploaded_file = request.FILES.get(f'new_field_file_{idx}')
                        timestamp = int(time.time())
                        ext = uploaded_file.name.split('.')[-1].lower()
                        filename = f'element_img_{world.id}_{timestamp}_{field_key}.{ext}'
                        file_path = default_storage.save(
                            f'element_images/{world.id}/{filename}',
                            ContentFile(uploaded_file.read())
                        )
                        value['image'] = default_storage.url(file_path)
                    value['caption'] = request.POST.get(f'new_field_caption_{idx}', '')
                    if value.get('image') or value.get('caption'):
                        data[field_key] = value

                elif field_type == 'gallery':
                    value = []
                    for key in request.FILES:
                        if key.startswith(f'new_field_gallery_{idx}_'):
                            uploaded_file = request.FILES[key]
                            timestamp = int(time.time())
                            ext = uploaded_file.name.split('.')[-1].lower()
                            filename = f'element_gallery_{world.id}_{timestamp}_{field_key}_{key}.{ext}'
                            file_path = default_storage.save(
                                f'element_gallery/{world.id}/{filename}',
                                ContentFile(uploaded_file.read())
                            )
                            value.append(default_storage.url(file_path))
                    if value:
                        data[field_key] = value

                elif field_type == 'select':
                    options = request.POST.get(f'new_field_options_{idx}', '')
                    fields_schema[field_key]['options'] = [opt.strip() for opt in options.split(',') if opt.strip()]
                    value = request.POST.get(f'new_field_value_{idx}', '')
                    if value:
                        data[field_key] = value

                elif field_type == 'multiselect':
                    options = request.POST.get(f'new_field_options_{idx}', '')
                    fields_schema[field_key]['options'] = [opt.strip() for opt in options.split(',') if opt.strip()]
                    value = request.POST.getlist(f'new_field_value_{idx}[]')
                    if value:
                        data[field_key] = value

                elif field_type == 'range':
                    range_config = request.POST.get(f'new_field_range_config_{idx}', '0,100')
                    parts = range_config.split(',')
                    fields_schema[field_key]['min'] = int(parts[0]) if len(parts) > 0 else 0
                    fields_schema[field_key]['max'] = int(parts[1]) if len(parts) > 1 else 100
                    value = request.POST.get(f'new_field_value_{idx}', '0')
                    if value:
                        data[field_key] = int(value)

                elif field_type == 'rating':
                    value = request.POST.get(f'new_field_value_{idx}', '0')
                    if value:
                        data[field_key] = int(value)

                elif field_type == 'tags':
                    tags = request.POST.get(f'new_field_value_{idx}', '')
                    if tags:
                        data[field_key] = [tag.strip() for tag in tags.split(',') if tag.strip()]

                elif field_type == 'file' and request.FILES.get(f'new_field_file_{idx}'):
                    uploaded_file = request.FILES.get(f'new_field_file_{idx}')
                    timestamp = int(time.time())
                    filename = f'element_file_{world.id}_{timestamp}_{field_key}_{uploaded_file.name}'
                    file_path = default_storage.save(
                        f'element_files/{world.id}/{filename}',
                        ContentFile(uploaded_file.read())
                    )
                    data[field_key] = default_storage.url(file_path)

                else:
                    value = request.POST.get(f'new_field_value_{idx}', '')
                    if value:
                        data[field_key] = value

        # Очистка пустых полей
        fields_schema = {k: v for k, v in fields_schema.items() if v.get('name') and v['name'].strip()}
        data = {k: v for k, v in data.items() if k in fields_schema or k == '_cover'}

        # Сохраняем изменения
        element.fields_schema = fields_schema
        element.data = data
        element.save()

        messages.success(request, f'Элемент "{element.name}" обновлён!')
        return redirect('elements:element_detail', world_id=world.id, element_id=element.id)

    return render(request, 'elements/element_edit.html', {
        'world': world,
        'element': element,
    })


@login_required
def element_delete(request, world_id, element_id):
    """Удаление элемента"""
    world = get_object_or_404(World, id=world_id, creator=request.user)
    element = get_object_or_404(Element, id=element_id, world=world)

    if request.method == 'POST':
        element_name = element.name
        element.delete()
        messages.success(request, f'Элемент "{element_name}" удалён!')
        return redirect('worlds:world_detail', world_id=world.id)

    return render(request, 'elements/element_confirm_delete.html', {
        'world': world,
        'element': element,
    })


@login_required
def get_category_elements(request, world_id, category_id):
    """AJAX получение элементов категории"""
    world = get_object_or_404(World, id=world_id, creator=request.user)
    category = get_object_or_404(ElementType, id=category_id, world=world)
    elements = category.elements.all()

    # Поиск по названию
    search_query = request.GET.get('search', '')
    if search_query:
        elements = elements.filter(name__icontains=search_query)

    data = []
    for element in elements:
        # Преобразуем data в словарь, если это строка
        element_data = element.data
        if isinstance(element_data, str):
            try:
                element_data = json.loads(element_data)
            except:
                element_data = {}

        cover_url = element_data.get('_cover') if element_data else None
        if not cover_url and element_data:
            for field_key, value in element_data.items():
                if isinstance(value, str) and value.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp')):
                    cover_url = value
                    break

        data.append({
            'id': element.id,
            'name': element.name,
            'category_name': category.name,
            'cover_url': cover_url,
            'created_at': element.created_at.strftime('%d.%m.%Y'),
        })

    return JsonResponse({'elements': data})