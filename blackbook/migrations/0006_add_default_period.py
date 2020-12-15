# Generated by Django 3.1.4 on 2020-12-15 21:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blackbook', '0005_add_budget_budgetperiod_model'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='default_period',
            field=models.CharField(choices=[('day', 'Daily'), ('week', 'Weekly'), ('month', 'Monthly'), ('quarter', 'Quarterly'), ('half_year', 'Every 6 months'), ('year', 'Yearly')], default='month', max_length=30),
        ),
    ]