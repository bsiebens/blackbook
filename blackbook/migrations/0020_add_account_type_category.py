# Generated by Django 3.1.4 on 2021-01-03 21:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blackbook', '0019_removed_link_from_certain_models_to_user_model'),
    ]

    operations = [
        migrations.AddField(
            model_name='accounttype',
            name='category',
            field=models.CharField(choices=[('assets', 'Assets'), ('liabilities', 'Liabilities'), ('expenses', 'Expenses'), ('income', 'Income')], default='assets', max_length=250),
        ),
    ]