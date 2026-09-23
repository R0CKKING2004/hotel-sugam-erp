from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Sum
from django.utils import timezone
from datetime import date

from .models import (
    Room,
    Guest,
    Booking,
    FoodItem,
    FoodOrder,
    Bill,
    Staff,
)


# =========================================================
# LOGIN / LOGOUT
# =========================================================

def login_view(request):

    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':

        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is not None:
            login(request, user)
            return redirect('dashboard')

        messages.error(
            request,
            'Invalid username or password.'
        )

    return render(request, 'login.html')


@login_required
def logout_view(request):

    logout(request)

    return redirect('login')


# =========================================================
# DASHBOARD - PUBLIC
# =========================================================

def dashboard(request):

    total_rooms = Room.objects.count()

    available_rooms = Room.objects.filter(
        status='Available'
    ).count()

    occupied_rooms = Room.objects.filter(
        status='Occupied'
    ).count()

    maintenance_rooms = Room.objects.filter(
        status='Maintenance'
    ).count()

    total_guests = Guest.objects.count()

    total_bookings = Booking.objects.count()

    paid_revenue = (
        Bill.objects
        .filter(payment_status='Paid')
        .aggregate(total=Sum('total_amount'))
        ['total'] or 0
    )

    pending_revenue = (
        Bill.objects
        .filter(payment_status='Pending')
        .aggregate(total=Sum('total_amount'))
        ['total'] or 0
    )

    today = timezone.localdate()

    today_checkins = Booking.objects.filter(
        check_in=today
    ).count()

    today_checkouts = Booking.objects.filter(
        check_out=today
    ).count()

    occupancy_percentage = 0

    if total_rooms > 0:
        occupancy_percentage = round(
            (occupied_rooms / total_rooms) * 100,
            2
        )

    context = {
        'total_rooms': total_rooms,
        'available_rooms': available_rooms,
        'occupied_rooms': occupied_rooms,
        'maintenance_rooms': maintenance_rooms,
        'occupancy_percentage': occupancy_percentage,

        'total_guests': total_guests,
        'total_bookings': total_bookings,

        'paid_revenue': paid_revenue,
        'pending_revenue': pending_revenue,

        'today_checkins': today_checkins,
        'today_checkouts': today_checkouts,

        'today_arrivals': today_checkins,
        'today_departures': today_checkouts,
    }

    return render(
        request,
        'dashboard.html',
        context
    )


# =========================================================
# ROOMS - PUBLIC VIEW
# =========================================================

def rooms(request):

    room_list = Room.objects.all().order_by(
        'room_number'
    )

    return render(
        request,
        'rooms.html',
        {
            'rooms': room_list
        }
    )


@login_required
def add_room(request):

    if request.method == 'POST':

        room_number = request.POST.get(
            'room_number'
        )

        room_type = request.POST.get(
            'room_type'
        )

        price_per_night = request.POST.get(
            'price_per_night'
        )

        status = request.POST.get(
            'status',
            'Available'
        )

        if Room.objects.filter(
            room_number=room_number
        ).exists():

            messages.error(
                request,
                'Room number already exists.'
            )

            return redirect('add_room')

        Room.objects.create(
            room_number=room_number,
            room_type=room_type,
            price_per_night=price_per_night,
            status=status
        )

        messages.success(
            request,
            'Room added successfully.'
        )

        return redirect('rooms')

    return render(
        request,
        'add_room.html'
    )


@login_required
def edit_room(request, room_id):

    room = get_object_or_404(
        Room,
        id=room_id
    )

    if request.method == 'POST':

        room.room_number = request.POST.get(
            'room_number'
        )

        room.room_type = request.POST.get(
            'room_type'
        )

        room.price_per_night = request.POST.get(
            'price_per_night'
        )

        room.status = request.POST.get(
            'status'
        )

        room.save()

        messages.success(
            request,
            'Room updated successfully.'
        )

        return redirect('rooms')

    return render(
        request,
        'edit_room.html',
        {
            'room': room
        }
    )


# =========================================================
# GUESTS - PUBLIC VIEW
# =========================================================

def guests(request):

    guest_list = Guest.objects.all().order_by(
        '-id'
    )

    return render(
        request,
        'guests.html',
        {
            'guests': guest_list
        }
    )


@login_required
def add_guest(request):

    if request.method == 'POST':

        Guest.objects.create(
            name=request.POST.get('name'),
            phone=request.POST.get('phone'),
            email=request.POST.get('email'),
            id_proof=request.POST.get('id_proof'),
            address=request.POST.get('address')
        )

        messages.success(
            request,
            'Guest added successfully.'
        )

        return redirect('guests')

    return render(
        request,
        'add_guest.html'
    )


@login_required
def edit_guest(request, guest_id):

    guest = get_object_or_404(
        Guest,
        id=guest_id
    )

    if request.method == 'POST':

        guest.name = request.POST.get(
            'name'
        )

        guest.phone = request.POST.get(
            'phone'
        )

        guest.email = request.POST.get(
            'email'
        )

        guest.id_proof = request.POST.get(
            'id_proof'
        )

        guest.address = request.POST.get(
            'address'
        )

        guest.save()

        messages.success(
            request,
            'Guest updated successfully.'
        )

        return redirect('guests')

    return render(
        request,
        'edit_guest.html',
        {
            'guest': guest
        }
    )


@login_required
def delete_guest(request, guest_id):

    guest = get_object_or_404(
        Guest,
        id=guest_id
    )

    guest.delete()

    messages.success(
        request,
        'Guest deleted successfully.'
    )

    return redirect('guests')


# =========================================================
# BOOKINGS - PUBLIC VIEW
# =========================================================

def bookings(request):

    booking_list = Booking.objects.select_related(
        'guest',
        'room'
    ).all().order_by(
        '-id'
    )

    return render(
        request,
        'bookings.html',
        {
            'bookings': booking_list
        }
    )


@login_required
def add_booking(request):

    if request.method == 'POST':

        guest_id = request.POST.get(
            'guest'
        )

        room_id = request.POST.get(
            'room'
        )

        check_in = request.POST.get(
            'check_in'
        )

        check_out = request.POST.get(
            'check_out'
        )

        number_of_guests = request.POST.get(
            'number_of_guests',
            1
        )

        guest = get_object_or_404(
            Guest,
            id=guest_id
        )

        room = get_object_or_404(
            Room,
            id=room_id
        )

        Booking.objects.create(
            guest=guest,
            room=room,
            check_in=check_in,
            check_out=check_out,
            number_of_guests=number_of_guests,
            status='Confirmed'
        )

        messages.success(
            request,
            'Booking created successfully.'
        )

        return redirect('bookings')

    guests_list = Guest.objects.all()

    rooms_list = Room.objects.filter(
        status='Available'
    )

    return render(
        request,
        'add_booking.html',
        {
            'guests': guests_list,
            'rooms': rooms_list
        }
    )


def available_rooms(request):

    rooms_list = Room.objects.filter(
        status='Available'
    ).values(
        'id',
        'room_number',
        'room_type',
        'price_per_night'
    )

    return JsonResponse(
        list(rooms_list),
        safe=False
    )


@login_required
def check_in_booking(request, booking_id):

    booking = get_object_or_404(
        Booking,
        id=booking_id
    )

    booking.status = 'Checked In'

    booking.room.status = 'Occupied'

    booking.room.save()

    booking.save()

    messages.success(
        request,
        'Guest checked in successfully.'
    )

    return redirect('bookings')


@login_required
def check_out_booking(request, booking_id):

    booking = get_object_or_404(
        Booking,
        id=booking_id
    )

    booking.status = 'Checked Out'

    booking.room.status = 'Available'

    booking.room.save()

    booking.save()

    messages.success(
        request,
        'Guest checked out successfully.'
    )

    return redirect('bookings')


@login_required
def edit_booking(request, booking_id):

    booking = get_object_or_404(
        Booking,
        id=booking_id
    )

    if request.method == 'POST':

        booking.guest_id = request.POST.get(
            'guest'
        )

        booking.room_id = request.POST.get(
            'room'
        )

        booking.check_in = request.POST.get(
            'check_in'
        )

        booking.check_out = request.POST.get(
            'check_out'
        )

        booking.number_of_guests = request.POST.get(
            'number_of_guests'
        )

        booking.status = request.POST.get(
            'status'
        )

        booking.save()

        messages.success(
            request,
            'Booking updated successfully.'
        )

        return redirect('bookings')

    guests_list = Guest.objects.all()

    rooms_list = Room.objects.all()

    return render(
        request,
        'edit_booking.html',
        {
            'booking': booking,
            'guests': guests_list,
            'rooms': rooms_list
        }
    )


@login_required
def cancel_booking(request, booking_id):

    booking = get_object_or_404(
        Booking,
        id=booking_id
    )

    booking.status = 'Cancelled'

    if booking.room.status == 'Occupied':
        booking.room.status = 'Available'
        booking.room.save()

    booking.save()

    messages.success(
        request,
        'Booking cancelled successfully.'
    )

    return redirect('bookings')


# =========================================================
# RESTAURANT - PUBLIC VIEW
# =========================================================

def restaurant(request):

    food_items = FoodItem.objects.filter(
        available=True
    ).order_by(
        'category',
        'name'
    )

    return render(
        request,
        'restaurant.html',
        {
            'food_items': food_items
        }
    )


@login_required
def add_food_order(request, food_id):

    food_item = get_object_or_404(
        FoodItem,
        id=food_id,
        available=True
    )

    if request.method == 'POST':

        booking_id = request.POST.get(
            'booking'
        )

        quantity = request.POST.get(
            'quantity',
            1
        )

        booking = None

        if booking_id:
            booking = get_object_or_404(
                Booking,
                id=booking_id
            )

        FoodOrder.objects.create(
            booking=booking,
            food_item=food_item,
            quantity=quantity
        )

        messages.success(
            request,
            'Food order added successfully.'
        )

        return redirect('restaurant')

    bookings_list = Booking.objects.filter(
        status__in=[
            'Confirmed',
            'Checked In'
        ]
    )

    return render(
        request,
        'add_food_order.html',
        {
            'food_item': food_item,
            'bookings': bookings_list
        }
    )


# =========================================================
# FOOD ORDERS - PUBLIC VIEW
# =========================================================

def food_orders(request):

    orders = FoodOrder.objects.select_related(
        'food_item',
        'booking',
        'booking__guest'
    ).all().order_by(
        '-order_date'
    )

    return render(
        request,
        'food_orders.html',
        {
            'orders': orders
        }
    )


@login_required
def update_food_order_status(
    request,
    order_id
):

    order = get_object_or_404(
        FoodOrder,
        id=order_id
    )

    if request.method == 'POST':

        order.status = request.POST.get(
            'status'
        )

        order.save()

        messages.success(
            request,
            'Food order status updated.'
        )

    return redirect('food_orders')


# =========================================================
# BILLING - PUBLIC VIEW
# =========================================================

def billing(request):

    bills = Bill.objects.select_related(
        'booking',
        'booking__guest',
        'booking__room'
    ).all().order_by(
        '-id'
    )

    return render(
        request,
        'billing.html',
        {
            'bills': bills
        }
    )


@login_required
def create_bill(request, booking_id):

    booking = get_object_or_404(
        Booking,
        id=booking_id
    )

    existing_bill = Bill.objects.filter(
        booking=booking
    ).first()

    if existing_bill:

        messages.info(
            request,
            'Bill already exists for this booking.'
        )

        return redirect('billing')

    room_charges = 0

    if booking.check_in and booking.check_out:

        nights = (
            booking.check_out -
            booking.check_in
        ).days

        if nights < 1:
            nights = 1

        room_charges = (
            booking.room.price_per_night *
            nights
        )

    food_charges = 0

    food_orders = FoodOrder.objects.filter(
        booking=booking
    )

    for order in food_orders:

        food_charges += (
            order.food_item.price *
            order.quantity
        )

    total_amount = (
        room_charges +
        food_charges
    )

    Bill.objects.create(
        booking=booking,
        room_charges=room_charges,
        food_charges=food_charges,
        total_amount=total_amount,
        payment_status='Pending'
    )

    messages.success(
        request,
        'Bill created successfully.'
    )

    return redirect('billing')


@login_required
def pay_bill(request, bill_id):

    bill = get_object_or_404(
        Bill,
        id=bill_id
    )

    if request.method == 'POST':

        bill.payment_status = 'Paid'

        bill.payment_method = request.POST.get(
            'payment_method'
        )

        bill.payment_date = timezone.now()

        bill.save()

        messages.success(
            request,
            'Payment recorded successfully.'
        )

    return redirect('billing')


def invoice(request, bill_id):

    bill = get_object_or_404(
        Bill,
        id=bill_id
    )

    return render(
        request,
        'invoice.html',
        {
            'bill': bill
        }
    )


# =========================================================
# STAFF - PUBLIC VIEW
# =========================================================

def staff(request):

    staff_list = Staff.objects.all().order_by(
        '-id'
    )

    return render(
        request,
        'staff.html',
        {
            'staff': staff_list
        }
    )


@login_required
def add_staff(request):

    if request.method == 'POST':

        Staff.objects.create(
            name=request.POST.get('name'),
            phone=request.POST.get('phone'),
            email=request.POST.get('email'),
            position=request.POST.get('position'),
            salary=request.POST.get('salary'),
            joining_date=request.POST.get('joining_date'),
            status=request.POST.get(
                'status',
                'Active'
            )
        )

        messages.success(
            request,
            'Staff added successfully.'
        )

        return redirect('staff')

    return render(
        request,
        'add_staff.html'
    )


@login_required
def edit_staff(request, staff_id):

    staff_member = get_object_or_404(
        Staff,
        id=staff_id
    )

    if request.method == 'POST':

        staff_member.name = request.POST.get(
            'name'
        )

        staff_member.phone = request.POST.get(
            'phone'
        )

        staff_member.email = request.POST.get(
            'email'
        )

        staff_member.position = request.POST.get(
            'position'
        )

        staff_member.salary = request.POST.get(
            'salary'
        )

        staff_member.joining_date = request.POST.get(
            'joining_date'
        )

        staff_member.status = request.POST.get(
            'status'
        )

        staff_member.save()

        messages.success(
            request,
            'Staff updated successfully.'
        )

        return redirect('staff')

    return render(
        request,
        'edit_staff.html',
        {
            'staff': staff_member
        }
    )


@login_required
def delete_staff(request, staff_id):

    staff_member = get_object_or_404(
        Staff,
        id=staff_id
    )

    staff_member.delete()

    messages.success(
        request,
        'Staff deleted successfully.'
    )

    return redirect('staff')


# =========================================================
# REPORTS - PUBLIC VIEW
# =========================================================

def reports(request):

    total_bookings = Booking.objects.count()

    total_guests = Guest.objects.count()

    total_rooms = Room.objects.count()

    paid_revenue = (
        Bill.objects
        .filter(payment_status='Paid')
        .aggregate(total=Sum('total_amount'))
        ['total'] or 0
    )

    pending_revenue = (
        Bill.objects
        .filter(payment_status='Pending')
        .aggregate(total=Sum('total_amount'))
        ['total'] or 0
    )

    room_revenue = (
        Bill.objects
        .filter(payment_status='Paid')
        .aggregate(total=Sum('room_charges'))
        ['total'] or 0
    )

    food_revenue = (
        Bill.objects
        .filter(payment_status='Paid')
        .aggregate(total=Sum('food_charges'))
        ['total'] or 0
    )

    context = {
        'total_bookings': total_bookings,
        'total_guests': total_guests,
        'total_rooms': total_rooms,

        'paid_revenue': paid_revenue,
        'pending_revenue': pending_revenue,

        'room_revenue': room_revenue,
        'food_revenue': food_revenue,
    }

    return render(
        request,
        'reports.html',
        context
    )