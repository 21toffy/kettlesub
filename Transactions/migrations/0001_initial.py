# Generated by Django 5.0.2 on 2024-02-24 19:21

import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('Wallet', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='TransactionModel',
            fields=[
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('is_deleted', models.BooleanField(default=False)),
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('active', models.BooleanField(default=False)),
                ('transaction_type', models.CharField(choices=[('Credit', 'Credit'), ('Debit', 'Debit')], max_length=10)),
                ('reference', models.CharField(max_length=100)),
                ('ext_reference', models.CharField(max_length=100, null=True)),
                ('description', models.CharField(max_length=255)),
                ('amount', models.DecimalField(decimal_places=2, max_digits=12)),
                ('status', models.CharField(choices=[('1', 'Processing'), ('2', 'Success'), ('3', 'Failed'), ('4', 'Declined'), ('4', 'Refunded')], max_length=255, null=True)),
                ('channel', models.CharField(choices=[('WEB', 'WEB'), ('APP', 'APP')], default='APP', max_length=255, null=True)),
                ('category', models.CharField(choices=[('BILLS', 'BILLS'), ('CARD', 'CARD'), ('REFERRARL', 'REFERRARL'), ('AIRTIME_PAYMENT', 'Airtime'), ('DATA_PAYMENT', 'Data'), ('ELECTRICITY_BILL', 'Electricity'), ('WALLET_TRANSFER', 'Wallet Transfer'), ('BANK_TRANSFER', 'Bank Tran Transfer'), ('CARD_MAINTANANCE', 'Card maintenance'), ('CARD_DEBIT', 'Card Debit'), ('CARD_CREDIT', 'Card Credit'), ('WALLET_CREDIT', 'Wallet Credit'), ('WALLET_DEBIT', 'Wallet Debit'), ('CABLE', 'CABLE'), ('CARD_FUNDING', 'Card Funding'), ('CARD_FUNDING_FEE', 'CARD_FUNDING_FEE')], max_length=50, null=True)),
                ('transaction_context', models.JSONField(blank=True, default=dict, null=True)),
                ('failed_transaction_context', models.JSONField(blank=True, default=dict, null=True)),
                ('balance_before', models.DecimalField(blank=True, decimal_places=2, default=0.0, max_digits=12, null=True)),
                ('balance_after', models.DecimalField(blank=True, decimal_places=2, default=0.0, max_digits=12, null=True)),
                ('currency', models.CharField(choices=[('NGN', 'NGN')], default='NGN', max_length=255, null=True)),
                ('user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ('wallet', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='Wallet.walletmodel')),
            ],
            options={
                'verbose_name': 'Transactions',
                'verbose_name_plural': 'Transactions',
                'db_table': 'transactions',
                'managed': True,
            },
        ),
    ]
