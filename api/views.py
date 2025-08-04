from rest_framework import viewsets, permissions, mixins
from .models import (
    ContactMessage, Journal, News, EditorialBoardMember, RecentIssueLink,
    Issue, Author, Keyword, Article
)
from .serializers import (
    ContactMessageSerializer, JournalSerializer, NewsSerializer, EditorialBoardMemberSerializer,
    RecentIssueLinkSerializer, IssueSerializer, AuthorSerializer, KeywordSerializer, ArticleSerializer
)


class IsAdminOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_staff


class ContactMessageViewSet(mixins.CreateModelMixin, mixins.ListModelMixin, mixins.RetrieveModelMixin,
                            mixins.DestroyModelMixin, viewsets.GenericViewSet):
    queryset = ContactMessage.objects.all()
    serializer_class = ContactMessageSerializer

    def get_permissions(self):
        if self.action == 'create':
            self.permission_classes = [permissions.AllowAny]
        else:
            self.permission_classes = [permissions.IsAdminUser]
        return super().get_permissions()


class JournalViewSet(viewsets.ModelViewSet):
    queryset = Journal.objects.all()
    serializer_class = JournalSerializer
    permission_classes = [IsAdminOrReadOnly]


class NewsViewSet(viewsets.ModelViewSet):
    queryset = News.objects.all()
    serializer_class = NewsSerializer
    permission_classes = [IsAdminOrReadOnly]


class EditorialBoardViewSet(viewsets.ModelViewSet):
    queryset = EditorialBoardMember.objects.all()
    serializer_class = EditorialBoardMemberSerializer
    permission_classes = [IsAdminOrReadOnly]

    def get_queryset(self):
        queryset = super().get_queryset()
        journal_short_name = self.request.query_params.get('journal', None)
        if journal_short_name:
            queryset = queryset.filter(journal__short_name=journal_short_name)
        return queryset


class RecentIssueLinkViewSet(viewsets.ModelViewSet):
    queryset = RecentIssueLink.objects.all()
    serializer_class = RecentIssueLinkSerializer
    permission_classes = [IsAdminOrReadOnly]


class AuthorViewSet(viewsets.ModelViewSet):
    queryset = Author.objects.all()
    serializer_class = AuthorSerializer
    permission_classes = [IsAdminOrReadOnly]


class KeywordViewSet(viewsets.ModelViewSet):
    queryset = Keyword.objects.all()
    serializer_class = KeywordSerializer
    permission_classes = [IsAdminOrReadOnly]


class IssueViewSet(viewsets.ModelViewSet):
    queryset = Issue.objects.all()
    serializer_class = IssueSerializer
    permission_classes = [IsAdminOrReadOnly]

    def get_queryset(self):
        queryset = super().get_queryset()
        journal_type = self.request.query_params.get('journal', None)
        is_current = self.request.query_params.get('current', None)

        if journal_type:
            queryset = queryset.filter(journal__short_name=journal_type)
        if is_current:
            is_current_bool = is_current.lower() in ['true', '1']
            queryset = queryset.filter(is_current=is_current_bool)

        return queryset


class ArticleViewSet(viewsets.ModelViewSet):
    queryset = Article.objects.all()
    serializer_class = ArticleSerializer
    permission_classes = [IsAdminOrReadOnly]