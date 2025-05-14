from django.urls import path 
from . import views

urlpatterns = [
    path('',views.home, name='home'),
    path('accounts/login/', views.login_view, name='login'),
    path('accounts/logout/', views.user_logout, name='logout'),
    path('upload-preview', views.upload_preview, name='upload_preview'),
    path('upload/<int:instance_id>/', views.upload, name='upload'),
    path('territories/', views.territory_list_page, name='territory_list'),
    path('territory/<str:territory_code>/', views.territory_detail, name='territory_detail'),
    path('download/all', views.download, name='download_all'),
    path('export-excel', views.export_excel, name='export_excel'),
    path('doctor/<int:instance_id>', views.doctor_view, name='doctor_view'),
    path('delete-doctor/<int:instance_id>', views.delete_doctor, name='delete_doctor'),
    path('admin',views.admin, name='admin_dashboard'),
]