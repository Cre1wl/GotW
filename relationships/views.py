import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q, Count
from .models import Relationship, RelationshipType, create_default_relationship_types
from worlds.models import World
from elements.models import Element


def get_character_category(world):
    """Получить категорию персонажей для мира"""
    # Ищем по разным вариантам названия (игнорируем регистр)
    for category in world.element_types.all():
        name_lower = category.name.lower()
        if name_lower in ['персонажи', 'персонаж', 'characters', 'character']:
            print(f"Найдена категория персонажей: {category.name}")
            return category

    print("Категория персонажей НЕ НАЙДЕНА")
    return None

def get_characters(world):
    """Получить всех персонажей мира"""
    character_category = get_character_category(world)
    if character_category:
        return world.elements.filter(element_type=character_category)
    return world.elements.none()


@login_required
def relationship_graph(request):
    """Выбор мира для просмотра графа связей"""
    worlds = World.objects.filter(creator=request.user)

    # Добавляем аннотации с количеством персонажей и связей для каждого мира
    for world in worlds:
        # Считаем персонажей
        character_category = get_character_category(world)
        if character_category:
            world.characters_count = world.elements.filter(element_type=character_category).count()
            # Считаем связи только между персонажами
            characters = world.elements.filter(element_type=character_category)
            world.relationships_count = Relationship.objects.filter(
                from_element__in=characters,
                to_element__in=characters
            ).count()
        else:
            world.characters_count = 0
            world.relationships_count = 0

    return render(request, 'relationships/world_select.html', {'worlds': worlds})


@login_required
def relationship_graph_detail(request, world_id):
    """Граф связей для конкретного мира"""
    world = get_object_or_404(World, id=world_id, creator=request.user)

    # Создаём ГЛОБАЛЬНЫЕ системные типы связей (world=None)
    create_default_relationship_types()

    characters = get_characters(world)
    character_category = get_character_category(world)

    relationships = Relationship.objects.filter(
        from_element__in=characters,
        to_element__in=characters
    )

    # Только глобальные типы и созданные пользователем
    relationship_types = RelationshipType.objects.filter(
        Q(world__isnull=True) | Q(created_by=request.user)
    ).distinct()

    return render(request, 'relationships/graph.html', {
        'world': world,
        'elements': characters,
        'relationships': relationships,
        'relationship_types': relationship_types,
        'has_character_category': character_category is not None,
    })


@login_required
def get_graph_data(request, world_id):
    """API для получения данных графа"""
    world = get_object_or_404(World, id=world_id, creator=request.user)

    # ТОЛЬКО ПЕРСОНАЖИ
    characters = get_characters(world)

    element_id = request.GET.get('element')

    if element_id:
        relationships = Relationship.objects.filter(
            Q(from_element__in=characters, to_element__in=characters) &
            (Q(from_element_id=element_id) | Q(to_element_id=element_id))
        )
        related_ids = set()
        for rel in relationships:
            related_ids.add(rel.from_element_id)
            related_ids.add(rel.to_element_id)
        characters = characters.filter(id__in=related_ids)
    else:
        relationships = Relationship.objects.filter(
            from_element__in=characters,
            to_element__in=characters
        )

    # Подсчёт связей
    element_connections = {}
    for character in characters:
        count = Relationship.objects.filter(
            Q(from_element=character) | Q(to_element=character)
        ).count()
        element_connections[character.id] = count

    max_connections = max(element_connections.values()) if element_connections else 1

    # Узлы
    nodes = []
    for character in characters:
        cover_url = None
        if character.data and isinstance(character.data, dict):
            cover_url = character.data.get('_cover')

        connections = element_connections.get(character.id, 0)
        base_size = 45
        size = base_size + (connections / max_connections) * 25 if max_connections > 0 else base_size

        nodes.append({
            'id': character.id,
            'name': character.name,
            'type': character.element_type.name,
            'color': '#8b5cf6',
            'cover_url': cover_url,
            'connections': connections,
            'size': min(size, 75),
        })

    # Рёбра с уникальными кривыми для множественных связей
    edges = []
    pair_edges = {}
    for rel in relationships:
        pair_key = tuple(sorted([rel.from_element_id, rel.to_element_id]))
        if pair_key not in pair_edges:
            pair_edges[pair_key] = []
        pair_edges[pair_key].append(rel)

    for pair_key, rels in pair_edges.items():
        for idx, rel in enumerate(rels):
            if len(rels) > 1:
                offset = (idx - (len(rels) - 1) / 2) * 0.3
                smooth_type = 'curvedCW' if offset > 0 else 'curvedCCW'
                roundness = abs(offset) + 0.15
            else:
                smooth_type = 'curvedCCW'
                roundness = 0.2

            edges.append({
                'id': rel.id,
                'from': rel.from_element_id,
                'to': rel.to_element_id,
                'label': rel.relationship_type.name,
                'color': rel.relationship_type.color,
                'width': rel.get_strength_width(),
                'strength': rel.strength,
                'type_id': rel.relationship_type_id,
                'description': rel.description,
                'arrows': '' if rel.relationship_type.is_bidirectional else 'to',
                'smooth': {'type': smooth_type, 'roundness': roundness}
            })

    return JsonResponse({'nodes': nodes, 'edges': edges})


@login_required
def relationship_list(request, world_id):
    """Список связей мира"""
    world = get_object_or_404(World, id=world_id, creator=request.user)
    characters = get_characters(world)

    relationships = Relationship.objects.filter(
        from_element__in=characters,
        to_element__in=characters
    ).select_related('from_element', 'to_element', 'relationship_type')

    element_id = request.GET.get('element')
    type_id = request.GET.get('type')

    if element_id:
        relationships = relationships.filter(
            Q(from_element_id=element_id) | Q(to_element_id=element_id)
        )
    if type_id:
        relationships = relationships.filter(relationship_type_id=type_id)

    relationship_types = RelationshipType.objects.filter(Q(world=world) | Q(world__isnull=True))

    return render(request, 'relationships/relationship_list.html', {
        'world': world,
        'relationships': relationships,
        'elements': characters,
        'relationship_types': relationship_types,
        'selected_element': element_id,
        'selected_type': type_id,
    })


@login_required
def relationship_create(request, world_id):
    """Создание связи"""
    world = get_object_or_404(World, id=world_id, creator=request.user)
    characters = get_characters(world)
    character_category = get_character_category(world)

    if not character_category:
        messages.error(request, 'Сначала создайте категорию для персонажей (например, "Персонажи" или "Characters")')
        return redirect('worlds:world_detail', world_id=world.id)

    create_default_relationship_types()

    # Только глобальные типы и созданные пользователем
    relationship_types = RelationshipType.objects.filter(
        Q(world__isnull=True) | Q(created_by=request.user)
    ).distinct()

    if request.method == 'POST':
        from_element_id = request.POST.get('from_element')
        to_element_id = request.POST.get('to_element')
        relationship_type_id = request.POST.get('relationship_type')
        description = request.POST.get('description', '')
        strength = request.POST.get('strength', 3)

        if from_element_id == to_element_id:
            messages.error(request, 'Нельзя создать связь персонажа с самим собой')
            return redirect('relationships:relationship_create', world_id=world.id)

        from_element = get_object_or_404(Element, id=from_element_id, world=world)
        to_element = get_object_or_404(Element, id=to_element_id, world=world)
        relationship_type = get_object_or_404(RelationshipType, id=relationship_type_id)

        if Relationship.objects.filter(
                from_element=from_element,
                to_element=to_element,
                relationship_type=relationship_type
        ).exists():
            messages.error(request, 'Такая связь уже существует')
            return redirect('relationships:relationship_create', world_id=world.id)

        relationship = Relationship.objects.create(
            from_element=from_element,
            to_element=to_element,
            relationship_type=relationship_type,
            description=description,
            strength=strength,
            created_by=request.user
        )

        messages.success(request, f'Связь создана!')
        return redirect('relationships:relationship_graph_detail', world_id=world.id)

    return render(request, 'relationships/relationship_form.html', {
        'world': world,
        'elements': characters,
        'relationship_types': relationship_types,
    })


@login_required
def relationship_create_ajax(request, world_id):
    """Создание связи через AJAX"""
    world = get_object_or_404(World, id=world_id, creator=request.user)
    character_category = get_character_category(world)

    if request.method == 'POST':
        from_element_id = request.POST.get('from_element')
        to_element_id = request.POST.get('to_element')
        relationship_type_id = request.POST.get('relationship_type')
        description = request.POST.get('description', '')
        strength = request.POST.get('strength', 3)

        if from_element_id == to_element_id:
            return JsonResponse({'error': 'Нельзя создать связь персонажа с самим собой'}, status=400)

        from_element = get_object_or_404(Element, id=from_element_id, world=world)
        to_element = get_object_or_404(Element, id=to_element_id, world=world)
        relationship_type = get_object_or_404(RelationshipType, id=relationship_type_id)

        if Relationship.objects.filter(
                from_element=from_element,
                to_element=to_element,
                relationship_type=relationship_type
        ).exists():
            return JsonResponse({'error': 'Такая связь уже существует'}, status=400)

        relationship = Relationship.objects.create(
            from_element=from_element,
            to_element=to_element,
            relationship_type=relationship_type,
            description=description,
            strength=int(strength),
            created_by=request.user
        )

        return JsonResponse({
            'success': True,
            'relationship': {
                'id': relationship.id,
                'from': relationship.from_element_id,
                'to': relationship.to_element_id,
                'label': relationship.relationship_type.name,
                'color': relationship.relationship_type.color,
                'width': relationship.get_strength_width(),
            }
        })

    return JsonResponse({'error': 'Invalid request'}, status=400)


@login_required
def relationship_edit(request, relationship_id):
    """Редактирование связи"""
    relationship = get_object_or_404(Relationship, id=relationship_id)
    world = relationship.from_element.world

    if world.creator != request.user:
        messages.error(request, 'У вас нет прав на редактирование этой связи')
        return redirect('relationships:relationship_graph')

    characters = get_characters(world)

    # Только глобальные типы и созданные пользователем
    relationship_types = RelationshipType.objects.filter(
        Q(world__isnull=True) | Q(created_by=request.user)
    ).distinct()

    if request.method == 'POST':
        to_element_id = request.POST.get('to_element')
        relationship_type_id = request.POST.get('relationship_type')
        description = request.POST.get('description', '')
        strength = request.POST.get('strength', 3)

        if relationship.from_element_id == int(to_element_id):
            messages.error(request, 'Нельзя создать связь персонажа с самим собой')
            return redirect('relationships:relationship_edit', relationship_id=relationship.id)

        relationship.to_element = get_object_or_404(Element, id=to_element_id, world=world)
        relationship.relationship_type = get_object_or_404(RelationshipType, id=relationship_type_id)
        relationship.description = description
        relationship.strength = strength
        relationship.save()

        messages.success(request, 'Связь обновлена!')
        return redirect('relationships:relationship_graph_detail', world_id=world.id)

    return render(request, 'relationships/relationship_form.html', {
        'world': world,
        'elements': characters,
        'relationship_types': relationship_types,
        'relationship': relationship,
    })


@login_required
def relationship_delete(request, relationship_id):
    """Удаление связи"""
    relationship = get_object_or_404(Relationship, id=relationship_id)

    if relationship.from_element.world.creator != request.user:
        messages.error(request, 'У вас нет прав на удаление этой связи')
        return redirect('relationships:relationship_graph')

    world_id = relationship.from_element.world.id

    if request.method == 'POST':
        relationship.delete()
        messages.success(request, 'Связь удалена!')

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True})

        return redirect('relationships:relationship_graph_detail', world_id=world_id)

    return render(request, 'relationships/relationship_confirm_delete.html', {
        'relationship': relationship
    })


@login_required
def relationship_type_list(request):
    """Список типов связей"""
    types = RelationshipType.objects.filter(
        Q(world__isnull=True, is_system=True) | Q(created_by=request.user)
    ).distinct().order_by('-is_system', 'name')

    return render(request, 'relationships/type_list.html', {'types': types})

@login_required
def relationship_type_create(request):
    """Создание типа связи"""
    worlds = World.objects.filter(creator=request.user)
    world_id = request.GET.get('world_id')

    if request.method == 'POST':
        name = request.POST.get('name')
        reverse_name = request.POST.get('reverse_name', '')
        description = request.POST.get('description', '')
        color = request.POST.get('color', '#8b5cf6')
        icon = request.POST.get('icon', 'link')
        is_bidirectional = request.POST.get('is_bidirectional') == 'on'
        world_id_post = request.POST.get('world')

        if name:
            world = None
            if world_id_post:
                world = get_object_or_404(World, id=world_id_post, creator=request.user)

            RelationshipType.objects.create(
                world=world,
                name=name,
                reverse_name=reverse_name,
                description=description,
                color=color,
                icon=icon,
                is_bidirectional=is_bidirectional,
                created_by=request.user
            )
            messages.success(request, f'Тип связи "{name}" создан!')

            if world_id_post:
                return redirect('relationships:relationship_graph_detail', world_id=world_id_post)
            return redirect('relationships:relationship_type_list')

    return render(request, 'relationships/type_form.html', {
        'worlds': worlds,
        'selected_world_id': world_id,
    })


@login_required
def relationship_type_edit(request, type_id):
    """Редактирование типа связи"""
    relationship_type = get_object_or_404(RelationshipType, id=type_id)

    if relationship_type.is_system:
        messages.error(request, 'Нельзя редактировать системные типы связей')
        return redirect('relationships:relationship_type_list')

    if relationship_type.created_by != request.user:
        messages.error(request, 'У вас нет прав на редактирование этого типа связи')
        return redirect('relationships:relationship_type_list')

    worlds = World.objects.filter(creator=request.user)

    if request.method == 'POST':
        relationship_type.name = request.POST.get('name')
        relationship_type.reverse_name = request.POST.get('reverse_name', '')
        relationship_type.description = request.POST.get('description', '')
        relationship_type.color = request.POST.get('color', '#8b5cf6')
        relationship_type.icon = request.POST.get('icon', 'link')
        relationship_type.is_bidirectional = request.POST.get('is_bidirectional') == 'on'

        world_id = request.POST.get('world')
        if world_id:
            relationship_type.world = get_object_or_404(World, id=world_id, creator=request.user)

        relationship_type.save()
        messages.success(request, f'Тип связи "{relationship_type.name}" обновлён!')
        return redirect('relationships:relationship_type_list')

    return render(request, 'relationships/type_form.html', {
        'type': relationship_type,
        'worlds': worlds
    })


@login_required
def relationship_type_delete(request, type_id):
    """Удаление типа связи"""
    relationship_type = get_object_or_404(RelationshipType, id=type_id)

    if relationship_type.is_system:
        messages.error(request, 'Нельзя удалить системный тип связи')
        return redirect('relationships:relationship_type_list')

    if relationship_type.created_by != request.user:
        messages.error(request, 'У вас нет прав на удаление этого типа связи')
        return redirect('relationships:relationship_type_list')

    if request.method == 'POST':
        name = relationship_type.name
        relationship_type.delete()
        messages.success(request, f'Тип связи "{name}" удалён!')
        return redirect('relationships:relationship_type_list')

    return render(request, 'relationships/type_confirm_delete.html', {
        'type': relationship_type
    })