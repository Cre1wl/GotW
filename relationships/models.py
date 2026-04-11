from django.db import models
from django.contrib.auth import get_user_model
from elements.models import Element
from worlds.models import World

User = get_user_model()


class RelationshipType(models.Model):
    """Тип связи между элементами"""

    world = models.ForeignKey(World, on_delete=models.CASCADE, related_name='relationship_types', null=True, blank=True)
    name = models.CharField(max_length=100, verbose_name="Название связи")
    reverse_name = models.CharField(max_length=100, blank=True, verbose_name="Обратное название")
    description = models.TextField(blank=True, verbose_name="Описание")
    color = models.CharField(max_length=20, default='#8b5cf6', verbose_name="Цвет")
    icon = models.CharField(max_length=50, default='link', verbose_name="Иконка")
    is_bidirectional = models.BooleanField(default=True, verbose_name="Двунаправленная")
    is_system = models.BooleanField(default=False, verbose_name="Системный тип")

    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Тип связи"
        verbose_name_plural = "Типы связей"
        ordering = ['-is_system', 'name']
        unique_together = [['world', 'name']]

    def __str__(self):
        return self.name


class Relationship(models.Model):
    """Связь между двумя элементами"""

    STRENGTH_CHOICES = [
        (1, 'Очень слабая'),
        (2, 'Слабая'),
        (3, 'Средняя'),
        (4, 'Сильная'),
        (5, 'Очень сильная'),
    ]

    from_element = models.ForeignKey(Element, on_delete=models.CASCADE, related_name='outgoing_relationships')
    to_element = models.ForeignKey(Element, on_delete=models.CASCADE, related_name='incoming_relationships')
    relationship_type = models.ForeignKey(RelationshipType, on_delete=models.CASCADE, related_name='relationships')

    description = models.TextField(blank=True, verbose_name="Описание")
    strength = models.IntegerField(choices=STRENGTH_CHOICES, default=3, verbose_name="Сила связи")

    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Связь"
        verbose_name_plural = "Связи"
        unique_together = ['from_element', 'to_element', 'relationship_type']
        indexes = [
            models.Index(fields=['from_element', 'to_element']),
            models.Index(fields=['from_element', 'relationship_type']),
        ]
        ordering = ['-created_at']

    def __str__(self):
        direction = "⟷" if self.relationship_type.is_bidirectional else "⟶"
        return f"{self.from_element.name} {direction} {self.to_element.name} ({self.relationship_type.name})"

    def get_strength_color(self):
        colors = {
            1: '#ef4444',
            2: '#f97316',
            3: '#eab308',
            4: '#10b981',
            5: '#06b6d4'
        }
        return colors.get(self.strength, '#64748b')

    def get_strength_width(self):
        return int(self.strength) * 1.5


def create_default_relationship_types(world=None):
    """Создаёт базовые типы связей (глобальные, не привязанные к конкретному миру)"""
    default_types = [
        {
            'name': 'Друг',
            'reverse_name': 'Друг',
            'color': '#10b981',
            'icon': 'user-friends',
            'is_bidirectional': True,
            'description': 'Близкие дружеские отношения, основанные на доверии и взаимопомощи.'
        },
        {
            'name': 'Враг',
            'reverse_name': 'Враг',
            'color': '#ef4444',
            'icon': 'user-ninja',
            'is_bidirectional': True,
            'description': 'Враждебные отношения, основанные на ненависти или противостоянии.'
        },
        {
            'name': 'Семья',
            'reverse_name': 'Семья',
            'color': '#f59e0b',
            'icon': 'home',
            'is_bidirectional': True,
            'description': 'Родственные связи: родители, дети, братья, сёстры.'
        },
        {
            'name': 'Знакомый',
            'reverse_name': 'Знакомый',
            'color': '#94a3b8',
            'icon': 'user',
            'is_bidirectional': True,
            'description': 'Поверхностное знакомство, без глубоких отношений.'
        },
        {
            'name': 'Любовь',
            'reverse_name': 'Любовь',
            'color': '#ec4899',
            'icon': 'heart',
            'is_bidirectional': True,
            'description': 'Романтические отношения, основанные на любви и привязанности.'
        },
        {
            'name': 'Учитель',
            'reverse_name': 'Ученик',
            'color': '#3b82f6',
            'icon': 'chalkboard-teacher',
            'is_bidirectional': False,
            'description': 'Отношения наставника и ученика, передача знаний и опыта.'
        },
        {
            'name': 'Начальник',
            'reverse_name': 'Подчинённый',
            'color': '#6366f1',
            'icon': 'crown',
            'is_bidirectional': False,
            'description': 'Иерархические отношения руководителя и подчинённого.'
        },
        {
            'name': 'Соперник',
            'reverse_name': 'Соперник',
            'color': '#f97316',
            'icon': 'fist-raised',
            'is_bidirectional': True,
            'description': 'Конкурентные отношения, стремление превзойти друг друга.'
        },
        {
            'name': 'Союзник',
            'reverse_name': 'Союзник',
            'color': '#14b8a6',
            'icon': 'handshake',
            'is_bidirectional': True,
            'description': 'Временное или постоянное объединение для достижения общих целей.'
        },
        {
            'name': 'Создатель',
            'reverse_name': 'Творение',
            'color': '#8b5cf6',
            'icon': 'magic',
            'is_bidirectional': False,
            'description': 'Отношения создателя и его творения.'
        },
        {
            'name': 'Владелец',
            'reverse_name': 'Владение',
            'color': '#d946ef',
            'icon': 'key',
            'is_bidirectional': False,
            'description': 'Отношения владения предметом, местом или существом.'
        },
        {
            'name': 'Член группы',
            'reverse_name': 'Член группы',
            'color': '#a855f7',
            'icon': 'users',
            'is_bidirectional': True,
            'description': 'Принадлежность к одной группе, команде, гильдии.'
        },
    ]

    for type_data in default_types:
        RelationshipType.objects.get_or_create(
            world=None,
            name=type_data['name'],
            defaults={
                'reverse_name': type_data['reverse_name'],
                'color': type_data['color'],
                'icon': type_data['icon'],
                'is_bidirectional': type_data['is_bidirectional'],
                'description': type_data['description'],
                'is_system': True
            }
        )