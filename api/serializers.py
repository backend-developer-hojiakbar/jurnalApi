from rest_framework import serializers
import json
from .models import (
    ContactMessage, ContactMessageFile, Journal, News, EditorialBoardMember, RecentIssueLink,
    Issue, Author, Keyword, Article, ArticleTranslation
)


class ContactMessageFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactMessageFile
        fields = ['id', 'file', 'uploaded_at']


class ContactMessageSerializer(serializers.ModelSerializer):
    files = ContactMessageFileSerializer(many=True, read_only=True)

    class Meta:
        model = ContactMessage
        fields = ['id', 'name', 'email', 'subject', 'message', 'is_read', 'created_at', 'files']


class JournalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Journal
        fields = '__all__'


class NewsSerializer(serializers.ModelSerializer):
    class Meta:
        model = News
        fields = '__all__'


class EditorialBoardMemberSerializer(serializers.ModelSerializer):
    journal_name = serializers.CharField(source='journal.name', read_only=True)
    journal_short_name = serializers.CharField(source='journal.short_name', read_only=True)

    class Meta:
        model = EditorialBoardMember
        fields = ['id', 'journal', 'journal_name', 'journal_short_name', 'full_name', 'position_description', 'role',
                  'order']


class RecentIssueLinkSerializer(serializers.ModelSerializer):
    class Meta:
        model = RecentIssueLink
        fields = '__all__'


class AuthorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Author
        fields = '__all__'

    def validate(self, data):
        # Ensure first_name and last_name are provided
        if not data.get('first_name') or not data.get('last_name'):
            raise serializers.ValidationError("Ism va familiya kiritilishi shart!")
        return data

    def validate_orcid_id(self, value):
        """Validate ORCID ID format"""
        if value and value.strip():
            # Remove any spaces and validate format
            orcid = value.strip()
            # ORCID ID should be in format: 0000-0000-0000-0000
            import re
            pattern = r'^\d{4}-\d{4}-\d{4}-\d{3}[\dX]$'
            if not re.match(pattern, orcid):
                raise serializers.ValidationError(
                    "ORCID ID noto'g'ri formatda. To'g'ri format: 0000-0002-1495-3967"
                )
        return value


class KeywordSerializer(serializers.ModelSerializer):
    class Meta:
        model = Keyword
        fields = '__all__'

    def validate_name(self, value):
        # Trim whitespace and check if not empty
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Kalit so'z nomi bo'sh bo'lishi mumkin emas!")
        return value


class ArticleTranslationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ArticleTranslation
        fields = ['language', 'title', 'abstract']


class ArticleSerializer(serializers.ModelSerializer):
    authors_read = AuthorSerializer(source='authors', many=True, read_only=True)
    keywords_read = KeywordSerializer(source='keywords', many=True, read_only=True)
    translations = ArticleTranslationSerializer(many=True, read_only=True)

    authors = serializers.PrimaryKeyRelatedField(queryset=Author.objects.all(), many=True, write_only=True,
                                                 required=False)
    keywords = serializers.PrimaryKeyRelatedField(queryset=Keyword.objects.all(), many=True, write_only=True,
                                                  required=False)
    translations_payload = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = Article
        fields = [
            'id', 'issue', 'doi', 'pages', 'authors', 'authors_read', 'keywords', 'keywords_read',
            'translations', 'translations_payload', 'references', 'views', 'article_file'
        ]

    def to_representation(self, instance):
        """Override to return authors_read and keywords_read as authors and keywords in read operations"""
        data = super().to_representation(instance)
        # Replace the write-only fields with read-only equivalents for output
        authors_data = data.pop('authors_read', [])
        keywords_data = data.pop('keywords_read', [])

        # Ensure authors and keywords are properly included
        data['authors'] = authors_data if authors_data is not None else []
        data['keywords'] = keywords_data if keywords_data is not None else []

        return data

    def create(self, validated_data):
        authors_data = validated_data.pop('authors', [])
        keywords_data = validated_data.pop('keywords', [])
        translations_str = validated_data.pop('translations_payload', '[]')

        try:
            translations_payload = json.loads(translations_str)
        except json.JSONDecodeError:
            translations_payload = []

        article = Article.objects.create(**validated_data)

        if authors_data:
            article.authors.set(authors_data)

        if keywords_data:
            article.keywords.set(keywords_data)

        for tr in translations_payload:
            ArticleTranslation.objects.create(article=article, **tr)

        return article

    def update(self, instance, validated_data):
        authors_data = validated_data.pop('authors', None)
        keywords_data = validated_data.pop('keywords', None)
        translations_str = validated_data.pop('translations_payload', None)

        for attr, val in validated_data.items():
            setattr(instance, attr, val)
        instance.save()

        if authors_data is not None:
            instance.authors.set(authors_data)

        if keywords_data is not None:
            instance.keywords.set(keywords_data)

        if translations_str is not None:
            try:
                translations_payload = json.loads(translations_str)
                instance.translations.all().delete()
                for tr in translations_payload:
                    ArticleTranslation.objects.create(article=instance, **tr)
            except json.JSONDecodeError:
                pass

        return instance


class IssueSerializer(serializers.ModelSerializer):
    articles = ArticleSerializer(many=True, read_only=True)
    journal_name = serializers.CharField(source='journal.name', read_only=True)
    journal_short_name = serializers.CharField(source='journal.short_name', read_only=True)
    current_status_display = serializers.SerializerMethodField()
    journal_type_display = serializers.CharField(source='get_journal_type_display', read_only=True)
    # Add fallback for journal_type if it's missing
    journal_type = serializers.SerializerMethodField()

    class Meta:
        model = Issue
        fields = ['id', 'journal', 'journal_name', 'journal_short_name', 'journal_type', 'journal_type_display',
                  'title', 'cover_image', 'pdf_file', 'published_date', 'is_current', 'current_status_display',
                  'articles']

    def get_journal_type(self, obj):
        # Return journal_type if set, otherwise fallback to journal.short_name
        if obj.journal_type:
            return obj.journal_type
        elif obj.journal and obj.journal.short_name:
            return obj.journal.short_name
        return 'QX'  # Default fallback

    def get_current_status_display(self, obj):
        if obj and obj.is_current:
            journal_type = self.get_journal_type(obj)
            return f"Joriy nashr ({journal_type})"
        return "Joriy emas"

    def validate(self, data):
        # Auto-set journal_type from journal if not provided
        if 'journal_type' not in data or not data['journal_type']:
            journal = data.get('journal')
            if journal:
                data['journal_type'] = journal.short_name

        # Ensure only one issue per journal type can be current
        if data.get('is_current', False):
            journal_type = data.get('journal_type')
            if journal_type:
                existing_current = Issue.objects.filter(journal_type=journal_type, is_current=True)
                if self.instance:
                    existing_current = existing_current.exclude(pk=self.instance.pk)

                if existing_current.exists():
                    current_issue = existing_current.first()
                    raise serializers.ValidationError({
                        'is_current': f"Bu jurnal turi ({journal_type}) uchun allaqachon joriy nashr mavjud: {current_issue.title}. "
                                      f"Avval uni joriy emasligini belgilang."
                    })
        return data

    def create(self, validated_data):
        # Ensure journal_type is set
        if 'journal_type' not in validated_data and 'journal' in validated_data:
            validated_data['journal_type'] = validated_data['journal'].short_name
        return super().create(validated_data)

    def update(self, instance, validated_data):
        # Ensure journal_type is set
        if 'journal_type' not in validated_data and 'journal' in validated_data:
            validated_data['journal_type'] = validated_data['journal'].short_name
        return super().update(instance, validated_data)