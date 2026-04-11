from django.urls import path
from . import views

app_name = 'galleries'

urlpatterns = [
    # Галереи
    path('content-type/<int:content_type_id>/object/<int:object_id>/',
         views.gallery_list, name='gallery_list'),
    path('content-type/<int:content_type_id>/object/<int:object_id>/create/',
         views.gallery_create, name='gallery_create'),
    path('<int:gallery_id>/', views.gallery_detail, name='gallery_detail'),
    path('<int:gallery_id>/edit/', views.gallery_edit, name='gallery_edit'),
    path('<int:gallery_id>/delete/', views.gallery_delete, name='gallery_delete'),

    # Изображения
    path('<int:gallery_id>/upload/', views.image_upload, name='image_upload'),
    path('<int:gallery_id>/multiple-upload/', views.multiple_image_upload, name='multiple_upload'),
    path('image/<int:image_id>/edit/', views.image_edit, name='image_edit'),
    path('image/<int:image_id>/delete/', views.image_delete, name='image_delete'),
    path('image/<int:image_id>/set-primary/', views.set_primary_image, name='set_primary'),
]