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

    class Meta:
        model = EditorialBoardMember
        fields = ['id', 'journal', 'journal_name', 'full_name', 'position_description', 'role', 'order']


class RecentIssueLinkSerializer(serializers.ModelSerializer):
    class Meta:
        model = RecentIssueLink
        fields = '__all__'


class AuthorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Author
        fields = '__all__'


class KeywordSerializer(serializers.ModelSerializer):
    class Meta:
        model = Keyword
        fields = '__all__'


class ArticleTranslationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ArticleTranslation
        fields = ['language', 'title', 'abstract']


class ArticleSerializer(serializers.ModelSerializer):
    authors = AuthorSerializer(many=True, read_only=True)
    keywords = KeywordSerializer(many=True, read_only=True)
    translations = ArticleTranslationSerializer(many=True, read_only=True)

    authors = serializers.PrimaryKeyRelatedField(queryset=Author.objects.all(), many=True, write_only=True,
                                                 required=False)
    keywords = serializers.PrimaryKeyRelatedField(queryset=Keyword.objects.all(), many=True, write_only=True,
                                                  required=False)
    translations_payload = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = Article
        fields = [
            'id', 'issue', 'doi', 'pages', 'authors', 'keywords',
            'translations', 'translations_payload', 'references', 'views', 'article_file'
        ]

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

    class Meta:
        model = Issue
        fields = ['id', 'journal', 'journal_name', 'title', 'cover_image', 'pdf_file', 'published_date', 'is_current',
                  'articles']