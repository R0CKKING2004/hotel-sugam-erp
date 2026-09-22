from django.urls import path
from . import views


urlpatterns = [

    # =====================================================
    # AUTHENTICATION
    # =====================================================

    path(
        'login/',
        views.login_view,
        name='login'
    ),

    path(
        'logout/',
        views.logout_view,
        name='logout'
    ),


    # =====================================================
    # DASHBOARD
    # =====================================================

    path(
        '',
        views.dashboard,
        name='dashboard'
    ),


    # =====================================================
    # ROOMS
    # =====================================================

    path(
        'rooms/',
        views.rooms,
        name='rooms'
    ),

    path(
        'rooms/add/',
        views.add_room,
        name='add_room'
    ),

    path(
        'rooms/edit/<int:room_id>/',
        views.edit_room,
        name='edit_room'
    ),


    # =====================================================
    # GUESTS
    # =====================================================

    path(
        'guests/',
        views.guests,
        name='guests'
    ),

    path(
        'guests/add/',
        views.add_guest,
        name='add_guest'
    ),

    path(
        'guests/edit/<int:guest_id>/',
        views.edit_guest,
        name='edit_guest'
    ),

    path(
        'guests/delete/<int:guest_id>/',
        views.delete_guest,
        name='delete_guest'
    ),


    # =====================================================
    # BOOKINGS
    # =====================================================

    path(
        'bookings/',
        views.bookings,
        name='bookings'
    ),

    path(
        'bookings/add/',
        views.add_booking,
        name='add_booking'
    ),

    path(
        'bookings/available-rooms/',
        views.available_rooms,
        name='available_rooms'
    ),

    path(
        'bookings/check-in/<int:booking_id>/',
        views.check_in_booking,
        name='check_in_booking'
    ),

    path(
        'bookings/check-out/<int:booking_id>/',
        views.check_out_booking,
        name='check_out_booking'
    ),

    path(
        'bookings/edit/<int:booking_id>/',
        views.edit_booking,
        name='edit_booking'
    ),

    path(
        'bookings/cancel/<int:booking_id>/',
        views.cancel_booking,
        name='cancel_booking'
    ),


    # =====================================================
    # RESTAURANT
    # =====================================================

    path(
        'restaurant/',
        views.restaurant,
        name='restaurant'
    ),

    path(
        'restaurant/order/<int:food_id>/',
        views.add_food_order,
        name='add_food_order'
    ),


    # =====================================================
    # FOOD ORDERS
    # =====================================================

    path(
        'food-orders/',
        views.food_orders,
        name='food_orders'
    ),

    path(
        'food-orders/status/<int:order_id>/',
        views.update_food_order_status,
        name='update_food_order_status'
    ),


    # =====================================================
    # BILLING
    # =====================================================

    path(
        'billing/',
        views.billing,
        name='billing'
    ),

    path(
        'billing/create/<int:booking_id>/',
        views.create_bill,
        name='create_bill'
    ),

    path(
        'billing/pay/<int:bill_id>/',
        views.pay_bill,
        name='pay_bill'
    ),

    path(
        'billing/invoice/<int:bill_id>/',
        views.invoice,
        name='invoice'
    ),


    # =====================================================
    # STAFF
    # =====================================================

    path(
        'staff/',
        views.staff,
        name='staff'
    ),

    path(
        'staff/add/',
        views.add_staff,
        name='add_staff'
    ),

    path(
        'staff/edit/<int:staff_id>/',
        views.edit_staff,
        name='edit_staff'
    ),

    path(
        'staff/delete/<int:staff_id>/',
        views.delete_staff,
        name='delete_staff'
    ),


    # =====================================================
    # REPORTS
    # =====================================================

    path(
        'reports/',
        views.reports,
        name='reports'
    ),

]