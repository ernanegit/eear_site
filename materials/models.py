from django.db import models
from django.contrib.auth import get_user_model
from courses.models import Subject

User = get_user_model()

class MaterialCategory(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, blank=True)
    
    class Meta:
        verbose_name_plural = "Material Categories"
    
    def __str__(self):
        return self.name

class Material(models.Model):
    MATERIAL_TYPES = [
        ('pdf', 'PDF'),
        ('doc', 'Documento'),
        ('video', 'Vídeo'),
        ('audio', 'Áudio'),
        ('link', 'Link Externo'),
        ('image', 'Imagem'),
    ]
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.ForeignKey(MaterialCategory, on_delete=models.CASCADE, related_name='materials')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='materials')
    material_type = models.CharField(max_length=20, choices=MATERIAL_TYPES, default='pdf')
    file = models.FileField(upload_to='materials/', blank=True, null=True)
    external_url = models.URLField(blank=True)
    thumbnail = models.ImageField(upload_to='materials/thumbs/', blank=True, null=True)
    is_premium = models.BooleanField(default=False)
    download_count = models.IntegerField(default=0)
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.title

class Download(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    material = models.ForeignKey(Material, on_delete=models.CASCADE)
    downloaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'material']
    
    def __str__(self):
        return f"{self.user.email} - {self.material.title}"