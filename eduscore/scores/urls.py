from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

r = DefaultRouter()
r.register('categories',views.CategoryViewSet, basename='category')
r.register('activities',views.ActivityViewSet, basename='activity')
r.register('users', views.UserViewSet, basename='user')
r.register('newsfeeds', views.NewsFeedViewSet, basename='newsfeed')
r.register('comments', views.CommentViewSet, basename='comment')
r.register('participation', views.ParticipationViewSet, basename='participation')
r.register('disciplined', views.DisciplinePointViewSet, basename='discipline')
r.register('report', views.ReportViewSet, basename='report')

urlpatterns = [
    path('',include(r.urls))
]