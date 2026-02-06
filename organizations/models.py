from django.db import models

class Company(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Companies"

class Document(models.Model):
    class DocType(models.TextChoices):
        POLICY = 'Policy', 'Policy'
        GUIDELINE = 'Guideline', 'Guideline'
        FAQ = 'FAQ', 'FAQ'
        FORM = 'Form', 'Form'
        OTHER = 'Other', 'Other'

    documentname = models.CharField(max_length=255)
    documentlink = models.URLField(max_length=500)
    doctype = models.CharField(max_length=20, choices=DocType.choices)
    isapplied = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.documentname