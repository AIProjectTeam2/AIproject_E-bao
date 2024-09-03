from django.db import models

# Create your models here.

class UserInteraction(models.Model):
    user_id = models.CharField(max_length=255, unique=True)
    first_cluster_label = models.IntegerField(null=True, blank=True)
    second_cluster_label = models.IntegerField(null=True, blank=True)
    user_input = models.TextField(null=True, blank=True)
    first_symptom = models.TextField(null=True, blank=True)
    second_symptom_1 = models.TextField(null=True, blank=True)
    second_symptom_2 = models.TextField(null=True, blank=True)
    user_status = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return self.user_id
    