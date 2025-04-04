# Generated by Django 5.1.7 on 2025-03-22 17:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("farm_core", "0004_productreview"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="npop_certificate_expiry_date",
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="user",
            name="npop_certificate_file",
            field=models.FileField(
                blank=True, null=True, upload_to="npop_certificates/"
            ),
        ),
        migrations.AddField(
            model_name="user",
            name="npop_certificate_issue_date",
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="user",
            name="npop_certificate_number",
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]
