from django.contrib import admin
from .models import TransactionModel


class TransactionModelAdmin(admin.ModelAdmin):
    list_display = ('user', 'wallet', 'transaction_type', 'reference', 'amount', 'status', 'channel', 'category',
                    'created_at')
    search_fields = ('user__email', 'wallet__id', 'reference', 'description')
    list_filter = ('transaction_type', 'status', 'channel', 'category')

    fieldsets = (
        (None, {'fields': ('user', 'wallet', 'transaction_type', 'reference', 'ext_reference')}),
        ('Transaction Details', {'fields': ('description', 'amount', 'status', 'channel', 'category',
                                            'transaction_context', 'failed_transaction_context', 'currency')}),
        ('Balance Details', {'fields': ('balance_before', 'balance_after')}),
        ('Dates', {'fields': ('created_at', 'updated_at')}),
    )

    readonly_fields = ('created_at', 'updated_at')


admin.site.register(TransactionModel, TransactionModelAdmin)
