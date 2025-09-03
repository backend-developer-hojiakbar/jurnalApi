from django.db import models

class ContactMessage(models.Model):
    name = models.CharField(max_length=255, verbose_name="Ismi")
    email = models.EmailField(verbose_name="Email")
    subject = models.CharField(max_length=255, verbose_name="Mavzu")
    message = models.TextField(verbose_name="Xabar")
    is_read = models.BooleanField(default=False, verbose_name="O'qilganmi?")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Yuborilgan sana")

    def __str__(self):
        return f"{self.name} - {self.subject}"

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Bog'lanish xabari"
        verbose_name_plural = "Bog'lanish xabarlari"

class ContactMessageFile(models.Model):
    message = models.ForeignKey(ContactMessage, on_delete=models.CASCADE, related_name='files')
    file = models.FileField(upload_to='contact_attachments/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.file.name

class Journal(models.Model):
    name = models.CharField(max_length=255, verbose_name="Jurnal nomi")
    short_name = models.CharField(max_length=10, unique=True, verbose_name="Qisqa nomi (masalan, QX yoki AI)")

    def __str__(self):
        return self.name

class News(models.Model):
    title = models.CharField(max_length=255, verbose_name="Sarlavha")
    content = models.TextField(verbose_name="Matn")
    image = models.ImageField(upload_to='news/', blank=True, null=True, verbose_name="Rasm")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Yaratilgan sana")

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Yangilik"
        verbose_name_plural = "Yangiliklar"

class EditorialBoardMember(models.Model):
    ROLE_CHOICES = (
        ('bosh_muharrir', 'Bosh muharrir'),
        ('masul_kotib', "Mas'ul kotib"),
        ('hayat_azosi', "Hay'at a'zosi"),
    )
    journal = models.ForeignKey(Journal, on_delete=models.CASCADE, related_name='board_members', verbose_name="Jurnal")
    full_name = models.CharField(max_length=255, verbose_name="F.I.O")
    position_description = models.TextField(verbose_name="Lavozimi va tavsifi")
    role = models.CharField(max_length=50, choices=ROLE_CHOICES, verbose_name="Roli")
    order = models.PositiveIntegerField(default=0, verbose_name="Tartib raqami")

    def __str__(self):
        return f"{self.full_name} ({self.journal.short_name})"

    class Meta:
        ordering = ['order']
        verbose_name = "Tahririyat a'zosi"
        verbose_name_plural = "Tahririyat a'zolari"

class RecentIssueLink(models.Model):
    title = models.CharField(max_length=100, verbose_name="Sarlavha (masalan, 2024 - №4)")
    link_to_issue = models.ForeignKey('Issue', on_delete=models.SET_NULL, null=True, blank=True,
                                      verbose_name="Bog'langan nashr")
    order = models.PositiveIntegerField(default=0, verbose_name="Tartib raqami")

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['order']
        verbose_name = "So'nggi nashr havolasi"
        verbose_name_plural = "So'nggi nashr havolalari"

class Issue(models.Model):
    journal = models.ForeignKey(Journal, on_delete=models.CASCADE, related_name='issues', verbose_name="Jurnal")
    title = models.CharField(max_length=255, verbose_name="Nashr sarlavhasi (masalan, 7-son, 2025)")
    cover_image = models.ImageField(upload_to='covers/', verbose_name="Muqova rasmi")
    pdf_file = models.FileField(upload_to='issues/', verbose_name="To'liq nashr (PDF)")
    published_date = models.DateField(verbose_name="Chop etilgan sana")
    is_current = models.BooleanField(default=False, verbose_name="Joriy nashrmi?")

    def __str__(self):
        return f"{self.journal.short_name} - {self.title}"

    class Meta:
        ordering = ['-published_date']
        verbose_name = "Nashr (son)"
        verbose_name_plural = "Nashrlar (sonlar)"

class Author(models.Model):
    last_name = models.CharField(max_length=100, verbose_name="Familiya")
    first_name = models.CharField(max_length=100, verbose_name="Ism")
    patronymic = models.CharField(max_length=100, blank=True, verbose_name="Otasining ismi")
    organization = models.CharField(max_length=255, blank=True, verbose_name="Tashkilot")
    position = models.CharField(max_length=255, blank=True, verbose_name="Lavozim")

    def __str__(self):
        return f"{self.last_name} {self.first_name}"

    class Meta:
        verbose_name = "Muallif"
        verbose_name_plural = "Mualliflar"

class Keyword(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="Nomi")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Kalit so'z"
        verbose_name_plural = "Kalit so'zlar"

class Article(models.Model):
    issue = models.ForeignKey(Issue, on_delete=models.CASCADE, related_name='articles', verbose_name="Nashr")
    doi = models.CharField(max_length=100, blank=True, verbose_name="DOI")
    pages = models.CharField(max_length=50, verbose_name="Sahifalar")
    authors = models.ManyToManyField(Author, related_name='articles', verbose_name="Mualliflar")
    keywords = models.ManyToManyField(Keyword, blank=True, verbose_name="Kalit so'zlar")
    references = models.TextField(blank=True, verbose_name="Foydalanilgan adabiyotlar")
    article_file = models.FileField(upload_to='articles/', blank=True, null=True, verbose_name="Maqola fayli (PDF)")
    views = models.PositiveIntegerField(default=0, verbose_name="Ko'rishlar soni")

    def __str__(self):
        first_translation = self.translations.first()
        return first_translation.title if first_translation else f"Maqola ID: {self.id}"

    class Meta:
        ordering = ['pages']
        verbose_name = "Maqola"
        verbose_name_plural = "Maqolalar"

class ArticleTranslation(models.Model):
    LANGUAGE_CHOICES = (
        ('uz', "O'zbek"),
        ('ru', 'Rus'),
        ('en', 'Ingliz'),
    )
    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name='translations')
    language = models.CharField(max_length=2, choices=LANGUAGE_CHOICES, verbose_name="Til")
    title = models.CharField(max_length=500, verbose_name="Maqola nomi")
    abstract = models.TextField(verbose_name="Annotatsiya")

    class Meta:
        unique_together = ('article', 'language')
        verbose_name = "Maqola tarjimasi"
        verbose_name_plural = "Maqola tarjimalari"

    def __str__(self):
        return f"{self.article} ({self.get_language_display()})"