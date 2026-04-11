from django.urls import path
from . import views

app_name = 'elements'

urlpatterns = [
    path('world/<int:world_id>/category/create-ajax/', views.category_create_ajax, name='category_create_ajax'),
    path('world/<int:world_id>/element/create/', views.element_create, name='element_create'),
    path('world/<int:world_id>/element/<int:element_id>/', views.element_detail, name='element_detail'),
    path('world/<int:world_id>/element/<int:element_id>/edit/', views.element_edit, name='element_edit'),
    path('world/<int:world_id>/element/<int:element_id>/delete/', views.element_delete, name='element_delete'),
    path('world/<int:world_id>/category/<int:category_id>/elements/', views.get_category_elements, name='category_elements'),
    path('category/<int:category_id>/update/', views.category_update, name='category_update'),
    path('category/<int:category_id>/delete/', views.category_delete, name='category_delete'),
]