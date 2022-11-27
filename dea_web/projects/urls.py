from django.urls import path
from .views import *
from . import views

urlpatterns = [
    path('', views.index, name='dea-index'),
    path('home/', views.index, name='projects-home'),
    path('create/', ProjectCreateView.as_view(), name='projects-create'),
    path('view/<int:pk>/', ProjectDetailView.as_view(), name='projects-detail'),
    path('edit/<int:pk>/', ProjectUpdateView.as_view(), name='projects-edit'),
    path('delete/<int:pk>/', ProjectDeleteView.as_view(), name='projects-delete'),
    path('list/', ProjectListView.as_view(), name='projects-list'),
    path('<int:pk>/file/create', ProjectFileCreateView.as_view(), name='projects-file-create'),
    path('<int:pk>/file/view/<int:fi>/', ProjectFileDetailView.as_view(), name='projects-file-detail'),
    path('<int:pk>/file/delete/<int:fi>/', ProjectFileDeleteView.as_view(), name='projects-file-delete'),
    path('<int:pk>/file/edit/<int:fi>/', ProjectFileUpdateView.as_view(), name='projects-file-edit'),
    path('<int:pk>/file/calculate-lp/<int:fi>/', calculate_lp, name='projects-file-calculate-lp'),
    path('<int:pk>/file/view/<int:fi>/results/view/<int:res>/', FileResultDetailView.as_view(), name='projects-file-result'),
    path('<int:pk>/file/lp-solve/<int:fi>/', lp_solve, name='lp-solve')
]
