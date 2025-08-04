from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'contact', views.ContactMessageViewSet, basename='contact')
router.register(r'journals', views.JournalViewSet)
router.register(r'news', views.NewsViewSet)
router.register(r'board-members', views.EditorialBoardViewSet, basename='boardmember')
router.register(r'recent-issues', views.RecentIssueLinkViewSet)
router.register(r'authors', views.AuthorViewSet)
router.register(r'keywords', views.KeywordViewSet)
router.register(r'issues', views.IssueViewSet)
router.register(r'articles', views.ArticleViewSet)

urlpatterns = [
    path('', include(router.urls)),
]