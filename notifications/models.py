from django.db import models
from organizations.models import Company

# Create your models here.

class SlackConfiguration(models.Model):
    company = models.OneToOneField(Company, on_delete=models.CASCADE, related_name='slack_config')
    bot_token = models.CharField(max_length=255)
    management_channel_id = models.CharField(max_length=100)
    slack_team_id = models.CharField(max_length=100, unique=True, help_text="Used to identify the company from Slack payloads")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Slack Config for {self.company.name}"
