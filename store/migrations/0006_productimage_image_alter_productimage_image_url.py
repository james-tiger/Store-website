# Generated by Django 5.0 on 2025-05-20 14:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0005_product_average_rating_product_rating'),
    ]

    operations = [
        migrations.AddField(
            model_name='productimage',
            name='image',
            field=models.ImageField(blank=True, null=True, upload_to='product_images/', verbose_name='Image File'),
        ),
        migrations.AlterField(
            model_name='productimage',
            name='image_url',
            field=models.URLField(blank=True, null=True, verbose_name='Image URL'),
        ),
    ]
