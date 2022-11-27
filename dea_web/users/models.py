from django.db import models
from django.contrib.auth.models import User


# Create your models here.
def user_directory(instance, filename):
    return 'user_uploads/{0}/project_files/{1}'.format(instance.user.id, filename)


class Tier(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    max_projects = models.IntegerField()

    def __str__(self):
        return "%s - Up to %s Projects" % (self.title, self.max_projects)


class UserTier(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE,related_name='user_tier',primary_key=True)
    tier = models.ForeignKey(Tier, on_delete=models.CASCADE)

    class Meta:
        ordering = ['tier', 'user']

    def __str__(self):
        return "%s - %s" % (self.user.username, self.tier.title)
