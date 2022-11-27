from django.contrib import admin
from .models import Project, File, FileResult

# Register your models here.
admin.site.register(Project)
admin.site.register(File)
admin.site.register(FileResult)
