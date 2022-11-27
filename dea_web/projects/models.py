from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.urls import reverse


def user_directory(instance, filename):
    return 'user_uploads/{0}/project_files/{1}'.format(instance.user.id, filename)

def user_results_directory(instance, filename):
    return 'user_uploads/{0}/project_files/{1}/results/{2}'.format(instance.file.user.id, instance.file.name,filename)


# Create your models here.
class Project(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    date_created = models.DateTimeField(default=timezone.now)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('projects-list')


class File(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField()
    file = models.FileField(default='default.txt', upload_to=user_directory)
    date_uploaded = models.DateTimeField(default=timezone.now)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('projects-detail', kwargs={'pk': self.project.id})


class FileResult(models.Model):
    file = models.ForeignKey(File, on_delete=models.CASCADE)
    date = models.DateTimeField(default=timezone.now)
    results_file = models.FileField(default='default.txt', upload_to=user_results_directory, null=True)

    def __str__(self):
        return "results for :"+self.file.name