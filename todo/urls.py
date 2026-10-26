from django.urls import path
from . import views


urlpatterns = [
	path('', views.TodoListView.as_view(), name='todos'),
	path('create_task/', views.CreateTaskView.as_view(), name='create_task'),
	path('delete_task/<int:pk>/', views.DeleteTaskView.as_view(), name='delete_task'),
	path('edit_task/<int:pk>/', views.UpdateTaskView.as_view(), name='edit_task'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),
    path('profile/', views.DashboardView.as_view(), name='profile'),
    path('edit_profile/<int:pk>', views.EditProfileView.as_view(), name='edit_profile'),
    path('users/', views.UsersListView.as_view(), name='users'),
    path('users/<int:pk>', views.UserDetailView.as_view(), name='user_detail'),
    path('task/<int:pk>/status/', views.update_task_status, name='update_task_status'),
]