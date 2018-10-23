from django.db import models

# Create your models here.


class User(models.Model):
    username = models.TextField()
    created = models.DateTimeField(auto_now=True)
    disabled = models.BooleanField(default=False)

    def __str__(self):
        return 'username={} created={} disabled={}'.format(
            self.username,
            self.created,
            self.disabled)