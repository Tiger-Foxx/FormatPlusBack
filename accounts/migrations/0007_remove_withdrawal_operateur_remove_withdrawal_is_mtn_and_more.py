# Generated by Django 5.1.1 on 2025-02-10 13:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0006_withdrawal_operateur_withdrawal_is_mtn_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='withdrawal',
            name='Operateur',
        ),
        migrations.RemoveField(
            model_name='withdrawal',
            name='is_MTN',
        ),
        migrations.AddField(
            model_name='withdrawal',
            name='country',
            field=models.CharField(default='Cameroun', max_length=250),
        ),
        migrations.AddField(
            model_name='withdrawal',
            name='operator',
            field=models.CharField(default='INCONNU', max_length=100),
        ),
    ]
