from django.contrib import admin

from .models import (
    Room,
    Guest,
    Booking,
    FoodItem,
    FoodOrder,
    Bill,
    Staff,
)


admin.site.register(Room)
admin.site.register(Guest)
admin.site.register(Booking)
admin.site.register(FoodItem)
admin.site.register(FoodOrder)
admin.site.register(Bill)
admin.site.register(Staff)