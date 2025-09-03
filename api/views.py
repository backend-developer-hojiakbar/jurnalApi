from rest_framework import viewsets, permissions, mixins, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from .models import (
    ContactMessage, ContactMessageFile, Journal, News, EditorialBoardMember, RecentIssueLink,
    Issue, Author, Keyword, Article
)
from .serializers import (
    ContactMessageSerializer, ContactMessageFileSerializer, JournalSerializer, NewsSerializer, EditorialBoardMemberSerializer,
    RecentIssueLinkSerializer, IssueSerializer, AuthorSerializer, KeywordSerializer, ArticleSerializer
)

class IsAdminOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_staff)

class ContactMessageViewSet(mixins.CreateModelMixin, mixins.ListModelMixin, mixins.RetrieveModelMixin,
                            mixins.DestroyModelMixin, viewsets.GenericViewSet):
    queryset = ContactMessage.objects.all()
    serializer_class = ContactMessageSerializer
    parser_classes = [MultiPartParser, FormParser]

    def get_permissions(self):
        if self.action == 'create' or self.action == 'upload_file':
            permission_classes = [permissions.AllowAny]
        else:
            permission_classes = [permissions.IsAdminUser]
        return [p() for p in permission_classes]

    @action(detail=True, methods=['post'], url_path='upload-file')
    def upload_file(self, request, pk=None):
        message = self.get_object()
        file = request.FILES.get('file')
        if not file:
            return Response({'detail':'Fayl topilmadi'}, status=status.HTTP_400_BAD_REQUEST)
        if file.size > 20 * 1024 * 1024:
            return Response({'detail':'Fayl hajmi 20MB dan kichik bo‘lishi kerak'}, status=status.HTTP_400_BAD_REQUEST)
        allowed = ['application/pdf', 'application/msword',
                   'application/vnd.openxmlformats-officedocument.wordprocessingml.document']
        if file.content_type not in allowed:
            return Response({'detail':'Faqat PDF yoki Word qabul qilinadi'}, status=status.HTTP_400_BAD_REQUEST)
        cmf = ContactMessageFile.objects.create(message=message, file=file)
        return Response(ContactMessageFileSerializer(cmf).data, status=status.HTTP_201_CREATED)

class JournalViewSet(viewsets.ModelViewSet):
    queryset = Journal.objects.all()
    serializer_class = JournalSerializer
    permission_classes = [IsAdminOrReadOnly]

class NewsViewSet(viewsets.ModelViewSet):
    queryset = News.objects.all()
    serializer_class = NewsSerializer
    permission_classes = [IsAdminOrReadOnly]
    parser_classes = [MultiPartParser, FormParser]

class EditorialBoardViewSet(viewsets.ModelViewSet):
    queryset = EditorialBoardMember.objects.all()
    serializer_class = EditorialBoardMemberSerializer
    permission_classes = [IsAdminOrReadOnly]

    def get_queryset(self):
        qs = super().get_queryset()
        journal_short_name = self.request.query_params.get('journal')
        if journal_short_name:
            qs = qs.filter(journal__short_name=journal_short_name)
        return qs

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
    parser_classes = [MultiPartParser, FormParser]

    def get_queryset(self):
        qs = super().get_queryset()
        journal_type = self.request.query_params.get('journal')
        is_current = self.request.query_params.get('current')
        if journal_type:
            qs = qs.filter(journal__short_name__iexact=journal_type)
        if is_current is not None:
            is_current_bool = str(is_current).lower() in ['true','1','yes','ha']
            qs = qs.filter(is_current=is_current_bool)
        return qs

class ArticleViewSet(viewsets.ModelViewSet):
    queryset = Article.objects.all()
    serializer_class = ArticleSerializer
    permission_classes = [IsAdminOrReadOnly]
    parser_classes = [MultiPartParser, FormParser]