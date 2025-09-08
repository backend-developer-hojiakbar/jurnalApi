from rest_framework import viewsets, permissions, mixins, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.views import APIView
from django.db.models import Q
from django.http import JsonResponse
from django.utils import timezone
from .models import (
    ContactMessage, ContactMessageFile, Journal, News, EditorialBoardMember, RecentIssueLink,
    Issue, Author, Keyword, Article
)
from .serializers import (
    ContactMessageSerializer, ContactMessageFileSerializer, JournalSerializer, NewsSerializer,
    EditorialBoardMemberSerializer,
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
            return Response({'detail': 'Fayl topilmadi'}, status=status.HTTP_400_BAD_REQUEST)
        if file.size > 20 * 1024 * 1024:
            return Response({'detail': 'Fayl hajmi 20MB dan kichik bo\'lishi kerak'},
                            status=status.HTTP_400_BAD_REQUEST)
        allowed = ['application/pdf', 'application/msword',
                   'application/vnd.openxmlformats-officedocument.wordprocessingml.document']
        if file.content_type not in allowed:
            return Response({'detail': 'Faqat PDF yoki Word qabul qilinadi'}, status=status.HTTP_400_BAD_REQUEST)
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
        # Optimize queries by prefetching related journal data
        qs = qs.select_related('journal').order_by('order', 'id')

        journal_short_name = self.request.query_params.get('journal')
        if journal_short_name:
            # Case-insensitive filtering to handle both 'QX'/'qx' and 'AI'/'ai'
            qs = qs.filter(journal__short_name__iexact=journal_short_name)
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
        # Optimize queries by prefetching related objects including article relationships
        qs = qs.prefetch_related(
            'articles__authors',
            'articles__keywords',
            'articles__translations'
        ).select_related('journal')

        journal_type = self.request.query_params.get('journal')
        is_current = self.request.query_params.get('current')

        if journal_type:
            # Filter by journal_type field directly (QX or AI)
            qs = qs.filter(journal_type__iexact=journal_type)

        if is_current is not None:
            is_current_bool = str(is_current).lower() in ['true', '1', 'yes', 'ha']
            qs = qs.filter(is_current=is_current_bool)

        return qs

    @action(detail=False, methods=['get'], url_path='current-issues')
    def current_issues(self, request):
        """Get current issues for all journals"""
        current_issues = Issue.objects.filter(is_current=True).select_related('journal')
        serializer = self.get_serializer(current_issues, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='by-journal-type/(?P<journal_type>[^/.]+)')
    def by_journal_type(self, request, journal_type=None):
        """Get issues by journal type (QX or AI)"""
        issues = self.get_queryset().filter(journal_type__iexact=journal_type)
        serializer = self.get_serializer(issues, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='current-by-type/(?P<journal_type>[^/.]+)')
    def current_by_type(self, request, journal_type=None):
        """Get current issue by journal type (QX or AI)"""
        try:
            issue = Issue.objects.get(journal_type__iexact=journal_type, is_current=True)
            serializer = self.get_serializer(issue)
            return Response(serializer.data)
        except Issue.DoesNotExist:
            return Response({'detail': f'Bu jurnal turi ({journal_type}) uchun joriy nashr topilmadi.'},
                            status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=['post'], url_path='set-current')
    def set_current(self, request, pk=None):
        """Set this issue as current for its journal type"""
        issue = self.get_object()

        # Remove current status from other issues of the same journal type
        Issue.objects.filter(journal_type=issue.journal_type, is_current=True).update(is_current=False)

        # Set this issue as current
        issue.is_current = True
        issue.save()

        serializer = self.get_serializer(issue)
        return Response({
            'detail': f'"{issue.title}" joriy nashr sifatida belgilandi ({issue.journal_type})',
            'issue': serializer.data
        })

        return Response({
            'detail': f'"{issue.title}" endi joriy nashr emas',
            'issue': serializer.data
        })

    @action(detail=False, methods=['get'], url_path='latest-year')
    def latest_year(self, request):
        """Get the year of the most recent issue"""
        try:
            latest_issue = Issue.objects.order_by('-published_date').first()
            if latest_issue:
                return Response({
                    'success': True,
                    'year': latest_issue.published_date.year,
                    'title': latest_issue.title,
                    'journal_type': latest_issue.journal_type
                })
            else:
                return Response({
                    'success': False,
                    'message': 'Hech qanday nashr topilmadi'
                })
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ArticleViewSet(viewsets.ModelViewSet):
    queryset = Article.objects.all()
    serializer_class = ArticleSerializer
    permission_classes = [IsAdminOrReadOnly]
    parser_classes = [MultiPartParser, FormParser]

    def get_queryset(self):
        qs = super().get_queryset()
        # Optimize database queries by prefetching related objects
        qs = qs.prefetch_related('authors', 'keywords', 'translations')

        issue_id = self.request.query_params.get('issue')
        journal_type = self.request.query_params.get('journal')

        if issue_id:
            qs = qs.filter(issue_id=issue_id)

        if journal_type:
            qs = qs.filter(issue__journal__short_name__iexact=journal_type)

        return qs

    def retrieve(self, request, *args, **kwargs):
        """Override retrieve to ensure proper data loading"""
        instance = self.get_object()

        # Debug: Print the actual data being returned
        serializer = self.get_serializer(instance)
        data = serializer.data

        # Log for debugging
        print(f"Article ID: {instance.id}")
        print(f"Authors count: {instance.authors.count()}")
        print(f"Authors data in response: {data.get('authors', [])}")
        print(f"Keywords count: {instance.keywords.count()}")
        print(f"Keywords data in response: {data.get('keywords', [])}")
        print(f"Translations count: {instance.translations.count()}")
        print(f"Translations data in response: {data.get('translations', [])}")

        return Response(data)


class HealthCheckView(APIView):
    """
    Simple health check endpoint to verify API is running
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        """
        Return API health status
        """
        try:
            # Check database connectivity by counting issues
            from .models import Issue
            issue_count = Issue.objects.count()

            health_data = {
                'status': 'healthy',
                'timestamp': timezone.now().isoformat(),
                'version': '1.0.0',
                'database': 'connected',
                'statistics': {
                    'total_issues': issue_count,
                },
                'message': 'Journal Management API is running successfully'
            }

            return Response(health_data, status=status.HTTP_200_OK)

        except Exception as e:
            health_data = {
                'status': 'unhealthy',
                'timestamp': timezone.now().isoformat(),
                'version': '1.0.0',
                'database': 'disconnected',
                'error': str(e),
                'message': 'Journal Management API encountered an error'
            }
            return Response(health_data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)