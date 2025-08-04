from rest_framework import serializers
from .models import (
    ContactMessage, Journal, News, EditorialBoardMember, RecentIssueLink,
    Issue, Author, Keyword, Article, ArticleTranslation
)


class ContactMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactMessage
        fields = '__all__'


class JournalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Journal
        fields = '__all__'


class NewsSerializer(serializers.ModelSerializer):
    class Meta:
        model = News
        fields = '__all__'


class EditorialBoardMemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = EditorialBoardMember
        fields = '__all__'


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

    class Meta:
        model = Article
        fields = ['id', 'issue', 'doi', 'pages', 'authors', 'keywords', 'translations', 'references', 'views',
                  'article_file']


class IssueSerializer(serializers.ModelSerializer):
    articles = ArticleSerializer(many=True, read_only=True)
    journal_name = serializers.CharField(source='journal.name', read_only=True)

    class Meta:
        model = Issue
        fields = ['id', 'journal', 'journal_name', 'title', 'cover_image', 'pdf_file', 'published_date', 'is_current',
                  'articles']