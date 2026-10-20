import uuid

from django.db import models
from django.utils import timezone


class Category(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)

    class Meta:
        managed = False
        db_table = 'content"."category'
        ordering = ["name"]
        verbose_name_plural = "categories"

    def __str__(self):
        return self.name


class Product(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, db_column="category_id")
    name = models.CharField(max_length=150)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'content"."product'
        ordering = ["name"]

    def __str__(self):
        return self.name


class Customer(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.CharField(max_length=150, unique=True, null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)

    class Meta:
        managed = False
        db_table = 'content"."customer'
        ordering = ["last_name", "first_name"]

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class DiningTable(models.Model):
    STATUS = [("AVAILABLE", "AVAILABLE"), ("OCCUPIED", "OCCUPIED"), ("RESERVED", "RESERVED")]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    table_number = models.IntegerField(unique=True)
    capacity = models.IntegerField()
    current_status = models.CharField(max_length=20, choices=STATUS, default="AVAILABLE")
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        managed = False
        db_table = 'content"."dining_table'
        ordering = ["table_number"]

    def __str__(self):
        return f"Mesa {self.table_number}"


class CustomerOrder(models.Model):
    TYPES = [("DINE_IN", "DINE_IN"), ("TAKEOUT", "TAKEOUT")]
    STATUS = [(s, s) for s in ("PENDING", "PREPARING", "READY", "COMPLETED", "CANCELED")]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True, db_column="customer_id")
    table = models.ForeignKey(DiningTable, on_delete=models.SET_NULL, null=True, blank=True, db_column="table_id")
    order_type = models.CharField(max_length=20, choices=TYPES)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS, default="PENDING")
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)

    class Meta:
        managed = False
        db_table = 'content"."customer_order'
        ordering = ["-created_at"]

    def __str__(self):
        return f"Pedido {self.id}"


class OrderLine(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey(CustomerOrder, on_delete=models.CASCADE, db_column="order_id")
    product = models.ForeignKey(Product, on_delete=models.PROTECT, db_column="product_id")
    quantity = models.IntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        managed = False
        db_table = 'content"."order_line'
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.quantity} x {self.product_id}"


class Promotion(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=150, unique=True)
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'content"."promotion'
        ordering = ["name"]

    def __str__(self):
        return self.name


class PromotionProduct(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    promotion = models.ForeignKey(Promotion, on_delete=models.CASCADE, db_column="promotion_id")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, db_column="product_id")

    class Meta:
        managed = False
        db_table = 'content"."promotion_product'
        ordering = ["id"]

    def __str__(self):
        return f"{self.promotion_id} / {self.product_id}"