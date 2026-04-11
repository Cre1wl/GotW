from django.urls import path
from . import views

app_name = 'relationships'

urlpatterns = [
    # Граф связей
    path('', views.relationship_graph, name='relationship_graph'),
    path('graph/<int:world_id>/', views.relationship_graph_detail, name='relationship_graph_detail'),
    path('graph/<int:world_id>/data/', views.get_graph_data, name='get_graph_data'),

    # Управление связями
    path('world/<int:world_id>/list/', views.relationship_list, name='relationship_list'),
    path('world/<int:world_id>/create/', views.relationship_create, name='relationship_create'),
    path('world/<int:world_id>/create/ajax/', views.relationship_create_ajax, name='relationship_create_ajax'),
    path('<int:relationship_id>/edit/', views.relationship_edit, name='relationship_edit'),
    path('<int:relationship_id>/delete/', views.relationship_delete, name='relationship_delete'),

    # Типы связей
    path('types/', views.relationship_type_list, name='relationship_type_list'),
    path('types/create/', views.relationship_type_create, name='relationship_type_create'),
    path('types/<int:type_id>/edit/', views.relationship_type_edit, name='relationship_type_edit'),
    path('types/<int:type_id>/delete/', views.relationship_type_delete, name='relationship_type_delete'),
]