# Generated by Django 5.0.2 on 2024-02-24 19:21

import django.core.validators
import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='WalletModel',
            fields=[
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('is_deleted', models.BooleanField(default=False)),
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('active', models.BooleanField(default=False)),
                ('balance', models.DecimalField(decimal_places=2, default=0.0, max_digits=20, validators=[django.core.validators.MinValueValidator(0.0)])),
                ('currency', models.CharField(max_length=255)),
                ('wallet_type', models.CharField(choices=[('MAIN', 'MAIN'), ('BONUS', 'BONUS')], max_length=255)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='user_wallet', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Wallet',
                'verbose_name_plural': 'Wallets',
                'db_table': 'wallets',
                'managed': True,
            },
        ),
    ]
