from decimal import Decimal

from django.contrib import admin
from django.core.exceptions import ValidationError
from django.forms.models import BaseInlineFormSet
from .models import CuentaLocal
from .models import (
    Categoria, Cliente, Empleado, ItemPedido, Mesa, Pedido, Plato,
    Promocion, PromocionPlato, Restaurante, Usuario,
)


@admin.register(Restaurante)
class RestauranteAdmin(admin.ModelAdmin):
    list_display = ("id", "nombre")
    search_fields = ("nombre",)


@admin.register(Plato)
class PlatoAdmin(admin.ModelAdmin):
    list_display = ("id", "nombre", "restaurante", "categoria", "precio", "disponible")
    list_filter = ("restaurante", "disponible", "categoria")
    search_fields = ("nombre", "restaurante__nombre")


class ItemPedidoFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()
        if any(self.errors):
            return
        restaurante_id = self.instance.restaurante_id
        for form in self.forms:
            if not form.cleaned_data or form.cleaned_data.get("DELETE"):
                continue
            plato = form.cleaned_data.get("plato")
            if plato and restaurante_id and plato.restaurante_id != restaurante_id:
                raise ValidationError(
                    "Todos los platos del pedido deben pertenecer al restaurante seleccionado."
                )


class ItemPedidoInline(admin.TabularInline):
    model = ItemPedido
    formset = ItemPedidoFormSet
    extra = 1
    min_num = 1
    validate_min = True
    fields = ("plato", "cantidad", "precio_unitario")
    readonly_fields = ("precio_unitario",)


@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display = ("id", "cliente", "restaurante", "estado", "fecha", "total")
    list_filter = ("estado", "restaurante")
    search_fields = ("cliente",)
    readonly_fields = ("total", "fecha")
    inlines = (ItemPedidoInline,)
    list_select_related = ("restaurante",)

    def save_formset(self, request, form, formset, change):
        if formset.model is not ItemPedido:
            super().save_formset(request, form, formset, change)
            return

        items = formset.save(commit=False)
        for item in formset.deleted_objects:
            item.delete()
        for item in items:
            if item.pk is None:
                
                item.precio_unitario = item.plato.precio
           
            item.save()
        formset.save_m2m()

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        pedido = form.instance
        total = sum(
            (item.precio_unitario * item.cantidad for item in pedido.items.all()),
            Decimal("0.00"),
        )
        Pedido.objects.filter(pk=pedido.pk).update(total=total)


@admin.register(Usuario)
class UsuarioAdmin(admin.ModelAdmin):
    list_display = ("id", "auth0_sub", "nombre", "apellido", "email", "telefono")
    search_fields = ("auth0_sub", "nombre", "apellido", "email")
    readonly_fields = ("auth0_sub",)

    def get_readonly_fields(self, request, obj=None):
      
        if obj is None:
            return ()
        return self.readonly_fields


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ("id", "usuario", "direccion", "fecha_registro")
    search_fields = ("usuario__auth0_sub", "usuario__nombre", "usuario__email", "direccion")
    list_select_related = ("usuario",)
    readonly_fields = ("fecha_registro",)


@admin.register(Empleado)
class EmpleadoAdmin(admin.ModelAdmin):
    list_display = ("id", "usuario", "restaurante", "cargo", "fecha_contratacion", "activo")
    list_filter = ("restaurante", "activo", "cargo")
    search_fields = ("usuario__auth0_sub", "usuario__nombre", "usuario__email", "cargo")
    list_select_related = ("usuario", "restaurante")


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ("id", "nombre")
    search_fields = ("nombre",)


@admin.register(Mesa)
class MesaAdmin(admin.ModelAdmin):
    list_display = ("id", "restaurante", "numero", "capacidad", "activa")
    list_filter = ("restaurante", "activa")
    search_fields = ("restaurante__nombre",)
    list_select_related = ("restaurante",)


class PromocionPlatoInline(admin.TabularInline):
    model = PromocionPlato
    extra = 1


@admin.register(Promocion)
class PromocionAdmin(admin.ModelAdmin):
    list_display = ("id", "nombre", "restaurante", "porcentaje_descuento", "activa")
    list_filter = ("restaurante", "activa")
    search_fields = ("nombre", "restaurante__nombre")
    list_select_related = ("restaurante",)
    inlines = (PromocionPlatoInline,)


@admin.register(PromocionPlato)
class PromocionPlatoAdmin(admin.ModelAdmin):
    list_display = ("id", "promocion", "plato")
    list_filter = ("promocion__restaurante",)
    search_fields = ("promocion__nombre", "plato__nombre")
    list_select_related = ("promocion", "plato")
@admin.register(CuentaLocal)
class CuentaLocalAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "username",
        "rol",
        "fecha_registro",
    )

    list_filter = ("rol",)
    search_fields = ("username",)
    ordering = ("-fecha_registro",)

    exclude = ("password_hash",)

    readonly_fields = (
        "username",
        "fecha_registro",
    )
    fields = (
    "username",
    "rol",
    "usuario",
    "fecha_registro",
    )

    autocomplete_fields = ("usuario",)

    list_select_related = ("usuario",)
   
    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return request.user.is_active and request.user.is_superuser