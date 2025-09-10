from django.contrib import admin
from .models import (
    ContactMessage, ContactMessageFile, Journal, News, EditorialBoardMember, RecentIssueLink,
    Issue, Author, Keyword, Article, ArticleTranslation
)

@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('name','email','subject','created_at','is_read')
    list_filter = ('is_read','created_at')
    search_fields = ('name','email','subject','message')
    list_editable = ('is_read',)

@admin.register(ContactMessageFile)
class ContactMessageFileAdmin(admin.ModelAdmin):
    list_display = ('message','file','uploaded_at')

@admin.register(Journal)
class JournalAdmin(admin.ModelAdmin):
    list_display = ('name','short_name')

@admin.register(News)
class NewsAdmin(admin.ModelAdmin):
    list_display = ('title','created_at')
    search_fields = ('title','content')

@admin.register(EditorialBoardMember)
class EditorialBoardMemberAdmin(admin.ModelAdmin):
    list_display = ('full_name','journal','role','order')
    list_filter = ('journal','role')
    list_editable = ('order',)
    search_fields = ('full_name',)

@admin.register(RecentIssueLink)
class RecentIssueLinkAdmin(admin.ModelAdmin):
    list_display = ('title','link_to_issue','order')
    list_editable = ('order',)

@admin.register(Issue)
class IssueAdmin(admin.ModelAdmin):
    list_display = ('title','journal','published_date','is_current')
    list_filter = ('journal','is_current','published_date')
    search_fields = ('title',)

@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    list_display = ('last_name', 'first_name', 'patronymic', 'orcid_id', 'organization')
    search_fields = ('last_name', 'first_name', 'patronymic', 'orcid_id')
    list_filter = ('organization',)

admin.site.register(Keyword)

class ArticleTranslationInline(admin.StackedInline):
    model = ArticleTranslation
    extra = 1

@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    inlines = [ArticleTranslationInline]
    list_display = ('__str__','issue','doi')
    list_filter = ('issue__journal','issue')
    search_fields = ('translations__title','doi')
    filter_horizontal = ('authors','keywords')