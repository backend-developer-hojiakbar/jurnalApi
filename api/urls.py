from django.urls import path, include
from django.views.generic import TemplateView
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

# Add URL patterns for development (debugging)
from django.conf import settings
if settings.DEBUG:
    urlpatterns += [
        # Additional debug URLs can be added here
        path('api/debug/', TemplateView.as_view(
            template_name='debug.html'
        ), name='api-debug'),
    ]