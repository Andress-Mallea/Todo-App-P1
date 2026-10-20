from django.contrib import admin

from . import models


class Base(admin.ModelAdmin):
    list_per_page = 50
    readonly_fields = ("created_at", "updated_at")


@admin.register(models.Category)
class CategoryAdmin(Base):
    list_display = ("name", "description", "created_at")
    search_fields = ("name",)


@admin.register(models.Product)
class ProductAdmin(Base):
    list_display = ("name", "category", "price", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name",)
    raw_id_fields = ("category",)


@admin.register(models.Customer)
class CustomerAdmin(Base):
    list_display = ("first_name", "last_name", "email")
    search_fields = ("first_name", "last_name", "email")


@admin.register(models.DiningTable)
class DiningTableAdmin(admin.ModelAdmin):
    list_display = ("table_number", "capacity", "current_status")
    list_filter = ("current_status",)
    list_per_page = 50
    readonly_fields = ("created_at",)


@admin.register(models.CustomerOrder)
class CustomerOrderAdmin(Base):
    list_display = ("id", "customer", "table", "order_type", "status", "total_amount", "created_at")
    list_filter = ("order_type", "status")
    raw_id_fields = ("customer", "table")


@admin.register(models.OrderLine)
class OrderLineAdmin(admin.ModelAdmin):
    list_display = ("order", "product", "quantity", "unit_price")
    list_per_page = 50
    raw_id_fields = ("order", "product")
    readonly_fields = ("created_at",)


@admin.register(models.Promotion)
class PromotionAdmin(Base):
    list_display = ("name", "discount_percentage", "start_date", "end_date", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name",)


@admin.register(models.PromotionProduct)
class PromotionProductAdmin(admin.ModelAdmin):
    list_display = ("promotion", "product")
    list_per_page = 50
    raw_id_fields = ("promotion", "product")