from django.contrib import admin
from Wallet.models.wallet import WalletModel


class WalletModelAdmin(admin.ModelAdmin):
    list_display = ('user', 'balance', 'currency', 'wallet_type')
    search_fields = ('user__email', 'currency', 'wallet_type')
    list_filter = ('wallet_type',)

    fieldsets = (
        (None, {'fields': ('user',)}),
        ('Wallet Info', {'fields': ('balance', 'currency', 'wallet_type')}),
        ('Dates', {'fields': ('created_at', 'updated_at')}),
    )

    readonly_fields = ('created_at', 'updated_at')


admin.site.register(WalletModel, WalletModelAdmin)
