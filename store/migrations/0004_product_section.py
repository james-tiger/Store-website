# Generated by Django 5.0 on 2025-05-19 18:23

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0003_section_alter_category_slug'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='section',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='store.section', verbose_name='Section'),
        ),
    ]
