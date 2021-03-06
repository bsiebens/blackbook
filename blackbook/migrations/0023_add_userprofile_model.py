# Generated by Django 3.1.4 on 2021-01-22 23:15

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import djmoney.models.fields


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('blackbook', '0022_cleanup'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('default_currency', djmoney.models.fields.CurrencyField(choices=[('ALL', 'Albanian Lek'), ('EUR', 'Euro'), ('AMD', 'Armenian Dram'), ('AZN', 'Azerbaijani Manat'), ('BYN', 'Belarusian Ruble'), ('BAM', 'Bosnia-Herzegovina Convertible Mark'), ('BGN', 'Bulgarian Lev'), ('HRK', 'Croatian Kuna'), ('CZK', 'Czech Koruna'), ('DKK', 'Danish Krone'), ('GEL', 'Georgian Lari'), ('HUF', 'Hungarian Forint'), ('ISK', 'Icelandic Króna'), ('CHF', 'Swiss Franc'), ('MDL', 'Moldovan Leu'), ('MKD', 'Macedonian Denar'), ('NOK', 'Norwegian Krone'), ('PLN', 'Polish Zloty'), ('RON', 'Romanian Leu'), ('RUB', 'Russian Ruble'), ('RSD', 'Serbian Dinar'), ('SEK', 'Swedish Krona'), ('TRY', 'Turkish Lira'), ('UAH', 'Ukrainian Hryvnia'), ('GBP', 'British Pound')], default='EUR', max_length=3)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
