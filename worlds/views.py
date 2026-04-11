from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from .models import World


@login_required
def library(request):
    """Библиотека миров пользователя"""
    worlds = request.user.worlds.all()

    search_query = request.GET.get('search', '')
    if search_query:
        worlds = worlds.filter(name__icontains=search_query)

    paginator = Paginator(worlds, 12)
    page_number = request.GET.get('page')
    worlds_page = paginator.get_page(page_number)

    return render(request, 'worlds/library.html', {
        'worlds': worlds_page,
        'search_query': search_query,
    })


@login_required
def world_detail(request, world_id):
    """Просмотр мира"""
    world = get_object_or_404(World, id=world_id, creator=request.user)

    from elements.models import ElementType, Element

    categories = world.element_types.all()
    elements = world.elements.all()

    # Поиск по элементам
    search_query = request.GET.get('search', '')
    if search_query:
        elements = elements.filter(name__icontains=search_query)

    stats = {
        'categories_count': categories.count(),
        'elements_count': elements.count(),
    }

    return render(request, 'worlds/world_detail.html', {
        'world': world,
        'categories': categories,
        'elements': elements,
        'stats': stats,
        'search_query': search_query,
    })

@login_required
def world_create(request):
    """Создание нового мира"""
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        cover_image = request.FILES.get('cover_image')

        if name and description:
            world = World.objects.create(
                name=name,
                description=description,
                cover_image=cover_image,
                creator=request.user
            )
            messages.success(request, f'Мир "{world.name}" успешно создан!')
            return redirect('worlds:world_detail', world_id=world.id)
        else:
            messages.error(request, 'Пожалуйста, заполните все поля')

    return render(request, 'worlds/world_form.html', {'title': 'Создание мира'})


@login_required
def world_settings(request, world_id):
    """Настройки мира"""
    world = get_object_or_404(World, id=world_id, creator=request.user)

    if request.method == 'POST':
        world.name = request.POST.get('name')
        world.description = request.POST.get('description')
        if request.FILES.get('cover_image'):
            world.cover_image = request.FILES.get('cover_image')
        world.save()
        messages.success(request, f'Настройки мира "{world.name}" обновлены!')
        return redirect('worlds:world_settings', world_id=world.id)

    return render(request, 'worlds/world_settings.html', {'world': world})


@login_required
def world_delete(request, world_id):
    """Удаление мира"""
    world = get_object_or_404(World, id=world_id, creator=request.user)

    if request.method == 'POST':
        world_name = world.name
        world.delete()
        messages.success(request, f'Мир "{world_name}" удален!')
        return redirect('worlds:library')

    return render(request, 'worlds/world_confirm_delete.html', {'world': world})


@login_required
def world_dashboard(request, world_id):
    """Аналитика мира"""
    world = get_object_or_404(World, id=world_id, creator=request.user)

    from elements.models import ElementType, Element

    total_elements = world.elements.count()
    total_types = world.element_types.count()

    # Цвета для категорий
    colors = ['#8b5cf6', '#14b8a6', '#ec4899', '#f59e0b', '#6366f1', '#10b981', '#ef4444', '#a855f7']

    element_types_stats = []
    for idx, element_type in enumerate(world.element_types.all()):
        elements_count = element_type.elements.count()
        percent = (elements_count / total_elements * 100) if total_elements > 0 else 0

        element_types_stats.append({
            'id': element_type.id,
            'name': element_type.name,
            'icon': 'cube',
            'color': colors[idx % len(colors)],
            'elements_count': elements_count,
            'percent': percent,
        })

    # Сортировка по количеству элементов (по убыванию)
    element_types_stats.sort(key=lambda x: x['elements_count'], reverse=True)

    recent_elements = world.elements.order_by('-created_at')[:8]

    return render(request, 'worlds/world_dashboard.html', {
        'world': world,
        'total_elements': total_elements,
        'total_types': total_types,
        'element_types_stats': element_types_stats,
        'recent_elements': recent_elements,
    })