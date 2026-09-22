from datetime import datetime

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import (
    Sum,
    F,
    DecimalField,
    ExpressionWrapper,
)

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
# AUTHENTICATION
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

            login(
                request,
                user
            )

            return redirect('dashboard')

        messages.error(
            request,
            'Invalid username or password.'
        )

    return render(
        request,
        'hotel_management/login.html'
    )


def logout_view(request):

    logout(request)

    messages.success(
        request,
        'You have been logged out successfully.'
    )

    return redirect('login')


# =========================================================
# DASHBOARD
# =========================================================

@login_required
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

    today = timezone.now().date()

    today_checkins = Booking.objects.filter(
        check_in=today
    ).count()

    today_checkouts = Booking.objects.filter(
        check_out=today
    ).count()

    paid_revenue = (
        Bill.objects
        .filter(payment_status='Paid')
        .aggregate(
            total=Sum('total_amount')
        )['total'] or 0
    )

    room_revenue = (
        Bill.objects
        .filter(payment_status='Paid')
        .aggregate(
            total=Sum('room_charges')
        )['total'] or 0
    )

    food_revenue = (
        Bill.objects
        .filter(payment_status='Paid')
        .aggregate(
            total=Sum('food_charges')
        )['total'] or 0
    )

    pending_bills = Bill.objects.filter(
        payment_status='Pending'
    ).count()

    recent_bookings = (
        Booking.objects
        .select_related('guest', 'room')
        .order_by('-id')[:5]
    )

    recent_food_orders = (
        FoodOrder.objects
        .select_related(
            'food_item',
            'booking__guest'
        )
        .order_by('-id')[:5]
    )

    paid_bills = (
        Bill.objects
        .filter(payment_status='Paid')
        .select_related(
            'booking__guest',
            'booking__room'
        )
        .order_by('-payment_date')[:5]
    )

    context = {
        'total_rooms': total_rooms,
        'available_rooms': available_rooms,
        'occupied_rooms': occupied_rooms,
        'maintenance_rooms': maintenance_rooms,
        'total_guests': total_guests,
        'total_bookings': total_bookings,
        'today_checkins': today_checkins,
        'today_checkouts': today_checkouts,
        'paid_revenue': paid_revenue,
        'room_revenue': room_revenue,
        'food_revenue': food_revenue,
        'pending_bills': pending_bills,
        'recent_bookings': recent_bookings,
        'recent_food_orders': recent_food_orders,
        'paid_bills': paid_bills,
    }

    return render(
        request,
        'hotel_management/dashboard.html',
        context
    )


# =========================================================
# ROOMS
# =========================================================

@login_required
def rooms(request):

    rooms_list = Room.objects.all().order_by('room_number')

    return render(
        request,
        'hotel_management/rooms.html',
        {
            'rooms': rooms_list
        }
    )


@login_required
def add_room(request):

    if request.method == 'POST':

        room_number = request.POST.get('room_number')
        room_type = request.POST.get('room_type')
        price_per_night = request.POST.get(
            'price_per_night'
        )
        status = request.POST.get('status')

        if not room_number or not room_type or not price_per_night:

            messages.error(
                request,
                'Please fill in all required fields.'
            )

            return redirect('add_room')

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
            status=status or 'Available'
        )

        messages.success(
            request,
            'Room added successfully.'
        )

        return redirect('rooms')

    return render(
        request,
        'hotel_management/add_room.html'
    )


@login_required
def edit_room(request, room_id):

    room = get_object_or_404(
        Room,
        id=room_id
    )

    if request.method == 'POST':

        room_number = request.POST.get('room_number')
        room_type = request.POST.get('room_type')
        price_per_night = request.POST.get(
            'price_per_night'
        )
        status = request.POST.get('status')

        if not room_number or not room_type or not price_per_night:

            messages.error(
                request,
                'Please fill in all required fields.'
            )

            return redirect(
                'edit_room',
                room_id=room.id
            )

        duplicate = (
            Room.objects
            .filter(room_number=room_number)
            .exclude(id=room.id)
            .exists()
        )

        if duplicate:

            messages.error(
                request,
                'Another room already uses this room number.'
            )

            return redirect(
                'edit_room',
                room_id=room.id
            )

        room.room_number = room_number
        room.room_type = room_type
        room.price_per_night = price_per_night
        room.status = status

        room.save()

        messages.success(
            request,
            'Room updated successfully.'
        )

        return redirect('rooms')

    return render(
        request,
        'hotel_management/edit_room.html',
        {
            'room': room
        }
    )


# =========================================================
# GUESTS
# =========================================================

@login_required
def guests(request):

    guests_list = Guest.objects.all().order_by('-id')

    return render(
        request,
        'hotel_management/guests.html',
        {
            'guests': guests_list
        }
    )


@login_required
def add_guest(request):

    if request.method == 'POST':

        name = request.POST.get('name')
        phone = request.POST.get('phone')
        email = request.POST.get('email')
        id_proof = request.POST.get('id_proof')
        address = request.POST.get('address')

        if not name or not phone:

            messages.error(
                request,
                'Name and phone number are required.'
            )

            return redirect('add_guest')

        Guest.objects.create(
            name=name,
            phone=phone,
            email=email,
            id_proof=id_proof,
            address=address
        )

        messages.success(
            request,
            'Guest added successfully.'
        )

        return redirect('guests')

    return render(
        request,
        'hotel_management/add_guest.html'
    )


@login_required
def edit_guest(request, guest_id):

    guest = get_object_or_404(
        Guest,
        id=guest_id
    )

    if request.method == 'POST':

        name = request.POST.get('name')
        phone = request.POST.get('phone')
        email = request.POST.get('email')
        id_proof = request.POST.get('id_proof')
        address = request.POST.get('address')

        if not name or not phone:

            messages.error(
                request,
                'Name and phone number are required.'
            )

            return redirect(
                'edit_guest',
                guest_id=guest.id
            )

        guest.name = name
        guest.phone = phone
        guest.email = email
        guest.id_proof = id_proof
        guest.address = address

        guest.save()

        messages.success(
            request,
            'Guest updated successfully.'
        )

        return redirect('guests')

    return render(
        request,
        'hotel_management/edit_guest.html',
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
# BOOKINGS
# =========================================================

@login_required
def bookings(request):

    bookings_list = (
        Booking.objects
        .select_related('guest', 'room')
        .order_by('-id')
    )

    total_bookings = bookings_list.count()

    confirmed_bookings = bookings_list.filter(
        status='Confirmed'
    ).count()

    checked_in_bookings = bookings_list.filter(
        status='Checked In'
    ).count()

    cancelled_bookings = bookings_list.filter(
        status='Cancelled'
    ).count()

    return render(
        request,
        'hotel_management/bookings.html',
        {
            'bookings': bookings_list,
            'total_bookings': total_bookings,
            'confirmed_bookings': confirmed_bookings,
            'checked_in_bookings': checked_in_bookings,
            'cancelled_bookings': cancelled_bookings,
        }
    )


@login_required
def add_booking(request):

    guests_list = Guest.objects.all().order_by('name')

    rooms_list = (
        Room.objects
        .filter(status='Available')
        .order_by('room_number')
    )

    if request.method == 'POST':

        guest_id = request.POST.get('guest')
        room_id = request.POST.get('room')
        check_in = request.POST.get('check_in')
        check_out = request.POST.get('check_out')
        number_of_guests = request.POST.get(
            'number_of_guests'
        )

        if not all([
            guest_id,
            room_id,
            check_in,
            check_out,
            number_of_guests
        ]):

            messages.error(
                request,
                'Please fill in all required fields.'
            )

            return redirect('add_booking')

        try:

            check_in_date = datetime.strptime(
                check_in,
                '%Y-%m-%d'
            ).date()

            check_out_date = datetime.strptime(
                check_out,
                '%Y-%m-%d'
            ).date()

        except ValueError:

            messages.error(
                request,
                'Invalid date format.'
            )

            return redirect('add_booking')

        if check_out_date <= check_in_date:

            messages.error(
                request,
                'Check-out date must be after check-in date.'
            )

            return redirect('add_booking')

        room = get_object_or_404(
            Room,
            id=room_id
        )

        if room.status == 'Maintenance':

            messages.error(
                request,
                f'Room {room.room_number} is under maintenance.'
            )

            return redirect('add_booking')

        overlapping_booking = (
            Booking.objects
            .filter(
                room=room,
                check_in__lt=check_out_date,
                check_out__gt=check_in_date
            )
            .exclude(
                status='Cancelled'
            )
            .exists()
        )

        if overlapping_booking:

            messages.error(
                request,
                f'Room {room.room_number} is already booked for these dates.'
            )

            return redirect('add_booking')

        Booking.objects.create(
            guest_id=guest_id,
            room=room,
            check_in=check_in_date,
            check_out=check_out_date,
            number_of_guests=number_of_guests,
            status='Confirmed'
        )

        room.status = 'Occupied'
        room.save()

        messages.success(
            request,
            f'Booking created successfully for Room {room.room_number}.'
        )

        return redirect('bookings')

    return render(
        request,
        'hotel_management/add_booking.html',
        {
            'guests': guests_list,
            'rooms': rooms_list,
        }
    )


@login_required
def available_rooms(request):

    check_in = request.GET.get('check_in')
    check_out = request.GET.get('check_out')

    if not check_in or not check_out:

        return JsonResponse({
            'rooms': []
        })

    try:

        check_in_date = datetime.strptime(
            check_in,
            '%Y-%m-%d'
        ).date()

        check_out_date = datetime.strptime(
            check_out,
            '%Y-%m-%d'
        ).date()

    except ValueError:

        return JsonResponse({
            'rooms': []
        })

    if check_out_date <= check_in_date:

        return JsonResponse({
            'rooms': []
        })

    booked_room_ids = (
        Booking.objects
        .filter(
            check_in__lt=check_out_date,
            check_out__gt=check_in_date
        )
        .exclude(
            status='Cancelled'
        )
        .values_list(
            'room_id',
            flat=True
        )
    )

    rooms_list = (
        Room.objects
        .exclude(
            id__in=booked_room_ids
        )
        .exclude(
            status='Maintenance'
        )
        .order_by('room_number')
    )

    room_data = []

    for room in rooms_list:

        room_data.append({
            'id': room.id,
            'room_number': room.room_number,
            'room_type': room.room_type,
            'price': str(room.price_per_night),
            'status': room.status,
        })

    return JsonResponse({
        'rooms': room_data
    })


# =========================================================
# CHECK-IN
# =========================================================

@login_required
def check_in_booking(request, booking_id):

    booking = get_object_or_404(
        Booking,
        id=booking_id
    )

    if booking.status != 'Confirmed':

        messages.error(
            request,
            'Only confirmed bookings can be checked in.'
        )

        return redirect('bookings')

    room = booking.room

    if room.status == 'Maintenance':

        messages.error(
            request,
            f'Room {room.room_number} is under maintenance.'
        )

        return redirect('bookings')

    booking.status = 'Checked In'
    booking.save()

    room.status = 'Occupied'
    room.save()

    messages.success(
        request,
        f'{booking.guest.name} checked in successfully.'
    )

    return redirect('bookings')


# =========================================================
# CHECK-OUT
# =========================================================

@login_required
def check_out_booking(request, booking_id):

    booking = get_object_or_404(
        Booking,
        id=booking_id
    )

    if booking.status != 'Checked In':

        messages.error(
            request,
            'Only checked-in bookings can be checked out.'
        )

        return redirect('bookings')

    booking.status = 'Checked Out'
    booking.save()

    room = booking.room

    active_booking = (
        Booking.objects
        .filter(
            room=room,
            status__in=[
                'Confirmed',
                'Checked In'
            ]
        )
        .exclude(
            id=booking.id
        )
        .exists()
    )

    if not active_booking:

        room.status = 'Available'
        room.save()

    messages.success(
        request,
        f'{booking.guest.name} checked out successfully.'
    )

    return redirect('bookings')


# =========================================================
# EDIT BOOKING
# =========================================================

@login_required
def edit_booking(request, booking_id):

    booking = get_object_or_404(
        Booking,
        id=booking_id
    )

    guests_list = Guest.objects.all().order_by('name')

    rooms_list = (
        Room.objects
        .exclude(status='Maintenance')
        .order_by('room_number')
    )

    if request.method == 'POST':

        guest_id = request.POST.get('guest')
        room_id = request.POST.get('room')
        check_in = request.POST.get('check_in')
        check_out = request.POST.get('check_out')
        number_of_guests = request.POST.get(
            'number_of_guests'
        )
        status = request.POST.get('status')

        if not all([
            guest_id,
            room_id,
            check_in,
            check_out,
            number_of_guests,
            status
        ]):

            messages.error(
                request,
                'Please fill in all required fields.'
            )

            return redirect(
                'edit_booking',
                booking_id=booking.id
            )

        try:

            check_in_date = datetime.strptime(
                check_in,
                '%Y-%m-%d'
            ).date()

            check_out_date = datetime.strptime(
                check_out,
                '%Y-%m-%d'
            ).date()

        except ValueError:

            messages.error(
                request,
                'Invalid date format.'
            )

            return redirect(
                'edit_booking',
                booking_id=booking.id
            )

        if check_out_date <= check_in_date:

            messages.error(
                request,
                'Check-out date must be after check-in date.'
            )

            return redirect(
                'edit_booking',
                booking_id=booking.id
            )

        room = get_object_or_404(
            Room,
            id=room_id
        )

        overlapping_booking = (
            Booking.objects
            .filter(
                room=room,
                check_in__lt=check_out_date,
                check_out__gt=check_in_date
            )
            .exclude(
                id=booking.id
            )
            .exclude(
                status='Cancelled'
            )
            .exists()
        )

        if overlapping_booking:

            messages.error(
                request,
                f'Room {room.room_number} is already booked for these dates.'
            )

            return redirect(
                'edit_booking',
                booking_id=booking.id
            )

        old_room = booking.room

        booking.guest_id = guest_id
        booking.room = room
        booking.check_in = check_in_date
        booking.check_out = check_out_date
        booking.number_of_guests = number_of_guests
        booking.status = status

        booking.save()

        if old_room.id != room.id:

            old_room_has_active_booking = (
                Booking.objects
                .filter(
                    room=old_room,
                    status__in=[
                        'Confirmed',
                        'Checked In'
                    ]
                )
                .exclude(
                    id=booking.id
                )
                .exists()
            )

            if not old_room_has_active_booking:

                old_room.status = 'Available'
                old_room.save()

        if status in [
            'Confirmed',
            'Checked In'
        ]:

            room.status = 'Occupied'
            room.save()

        elif status in [
            'Checked Out',
            'Cancelled'
        ]:

            room.status = 'Available'
            room.save()

        messages.success(
            request,
            'Booking updated successfully.'
        )

        return redirect('bookings')

    return render(
        request,
        'hotel_management/edit_booking.html',
        {
            'booking': booking,
            'guests': guests_list,
            'rooms': rooms_list,
        }
    )


# =========================================================
# CANCEL BOOKING
# =========================================================

@login_required
def cancel_booking(request, booking_id):

    booking = get_object_or_404(
        Booking,
        id=booking_id
    )

    booking.status = 'Cancelled'
    booking.save()

    room = booking.room

    active_booking = (
        Booking.objects
        .filter(
            room=room,
            status__in=[
                'Confirmed',
                'Checked In'
            ]
        )
        .exclude(
            id=booking.id
        )
        .exists()
    )

    if not active_booking:

        room.status = 'Available'
        room.save()

    messages.success(
        request,
        'Booking cancelled successfully.'
    )

    return redirect('bookings')


# =========================================================
# RESTAURANT
# =========================================================

@login_required
def restaurant(request):

    food_items = (
        FoodItem.objects
        .filter(available=True)
        .order_by('category', 'name')
    )

    return render(
        request,
        'hotel_management/restaurant.html',
        {
            'food_items': food_items
        }
    )


@login_required
def add_food_order(request, food_id):

    food_item = get_object_or_404(
        FoodItem,
        id=food_id
    )

    if request.method == 'POST':

        booking_id = request.POST.get('booking')
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
            quantity=quantity,
            status='Pending'
        )

        messages.success(
            request,
            f'{food_item.name} order added successfully.'
        )

        return redirect('food_orders')

    bookings_list = (
        Booking.objects
        .select_related('guest', 'room')
        .filter(
            status__in=[
                'Confirmed',
                'Checked In'
            ]
        )
        .order_by('-id')
    )

    return render(
        request,
        'hotel_management/add_food_order.html',
        {
            'food_item': food_item,
            'bookings': bookings_list,
        }
    )


# =========================================================
# FOOD ORDERS
# =========================================================

@login_required
def food_orders(request):

    orders = (
        FoodOrder.objects
        .select_related(
            'food_item',
            'booking__guest',
            'booking__room'
        )
        .order_by('-order_date')
    )

    return render(
        request,
        'hotel_management/food_orders.html',
        {
            'orders': orders
        }
    )


@login_required
def update_food_order_status(request, order_id):

    order = get_object_or_404(
        FoodOrder,
        id=order_id
    )

    if request.method == 'POST':

        status = request.POST.get('status')

        valid_statuses = [
            'Pending',
            'Preparing',
            'Completed',
            'Cancelled'
        ]

        if status in valid_statuses:

            order.status = status
            order.save()

            messages.success(
                request,
                'Food order status updated.'
            )

    return redirect('food_orders')


# =========================================================
# BILLING
# =========================================================

@login_required
def billing(request):

    bills = (
        Bill.objects
        .select_related(
            'booking__guest',
            'booking__room'
        )
        .order_by('-id')
    )

    bills_count = bills.count()

    paid_bills = bills.filter(
        payment_status='Paid'
    ).count()

    pending_bills = bills.filter(
        payment_status='Pending'
    ).count()

    paid_revenue = (
        bills
        .filter(payment_status='Paid')
        .aggregate(
            total=Sum('total_amount')
        )['total'] or 0
    )

    billed_booking_ids = bills.values_list(
        'booking_id',
        flat=True
    )

    bookings_ready = (
        Booking.objects
        .select_related('guest', 'room')
        .filter(
            status__in=[
                'Checked Out',
                'Checked In',
                'Confirmed'
            ]
        )
        .exclude(
            id__in=billed_booking_ids
        )
        .order_by('-id')
    )

    return render(
        request,
        'hotel_management/billing.html',
        {
            'bills': bills,
            'bills_count': bills_count,
            'paid_bills': paid_bills,
            'pending_bills': pending_bills,
            'paid_revenue': paid_revenue,
            'bookings_ready': bookings_ready,
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
            'A bill already exists for this booking.'
        )

        return redirect('billing')

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

    food_charges = (
        FoodOrder.objects
        .filter(
            booking=booking
        )
        .exclude(
            status='Cancelled'
        )
        .aggregate(
            total=Sum(
                ExpressionWrapper(
                    F('food_item__price') *
                    F('quantity'),
                    output_field=DecimalField(
                        max_digits=10,
                        decimal_places=2
                    )
                )
            )
        )['total'] or 0
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
        'Bill generated successfully.'
    )

    return redirect('billing')


@login_required
def pay_bill(request, bill_id):

    bill = get_object_or_404(
        Bill,
        id=bill_id
    )

    if request.method == 'POST':

        payment_method = request.POST.get(
            'payment_method'
        )

        valid_methods = [
            'Cash',
            'Card',
            'UPI'
        ]

        if payment_method not in valid_methods:

            messages.error(
                request,
                'Please select a valid payment method.'
            )

            return redirect('billing')

        bill.payment_status = 'Paid'
        bill.payment_method = payment_method
        bill.payment_date = timezone.now()

        bill.save()

        messages.success(
            request,
            'Payment completed successfully.'
        )

    return redirect('billing')


@login_required
def invoice(request, bill_id):

    bill = get_object_or_404(
        Bill.objects.select_related(
            'booking__guest',
            'booking__room'
        ),
        id=bill_id
    )

    return render(
        request,
        'hotel_management/invoice.html',
        {
            'bill': bill
        }
    )


# =========================================================
# STAFF
# =========================================================

@login_required
def staff(request):

    staff_list = Staff.objects.all().order_by('name')

    return render(
        request,
        'hotel_management/staff.html',
        {
            'staff': staff_list
        }
    )


@login_required
def add_staff(request):

    if request.method == 'POST':

        name = request.POST.get('name')
        phone = request.POST.get('phone')
        email = request.POST.get('email')
        position = request.POST.get('position')
        salary = request.POST.get('salary')
        joining_date = request.POST.get('joining_date')
        status = request.POST.get(
            'status',
            'Active'
        )

        if not name or not phone or not position or not salary or not joining_date:

            messages.error(
                request,
                'Please fill in all required fields.'
            )

            return redirect('add_staff')

        Staff.objects.create(
            name=name,
            phone=phone,
            email=email,
            position=position,
            salary=salary,
            joining_date=joining_date,
            status=status
        )

        messages.success(
            request,
            'Staff member added successfully.'
        )

        return redirect('staff')

    return render(
        request,
        'hotel_management/add_staff.html'
    )


@login_required
def edit_staff(request, staff_id):

    staff_member = get_object_or_404(
        Staff,
        id=staff_id
    )

    if request.method == 'POST':

        staff_member.name = request.POST.get('name')
        staff_member.phone = request.POST.get('phone')
        staff_member.email = request.POST.get('email')
        staff_member.position = request.POST.get('position')
        staff_member.salary = request.POST.get('salary')
        staff_member.joining_date = request.POST.get(
            'joining_date'
        )
        staff_member.status = request.POST.get(
            'status'
        )

        staff_member.save()

        messages.success(
            request,
            'Staff member updated successfully.'
        )

        return redirect('staff')

    return render(
        request,
        'hotel_management/edit_staff.html',
        {
            'staff_member': staff_member
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
        'Staff member deleted successfully.'
    )

    return redirect('staff')


# =========================================================
# REPORTS
# =========================================================

@login_required
def reports(request):

    total_bookings = Booking.objects.count()

    total_guests = Guest.objects.count()

    total_rooms = Room.objects.count()

    paid_revenue = (
        Bill.objects
        .filter(payment_status='Paid')
        .aggregate(
            total=Sum('total_amount')
        )['total'] or 0
    )

    room_revenue = (
        Bill.objects
        .filter(payment_status='Paid')
        .aggregate(
            total=Sum('room_charges')
        )['total'] or 0
    )

    food_revenue = (
        Bill.objects
        .filter(payment_status='Paid')
        .aggregate(
            total=Sum('food_charges')
        )['total'] or 0
    )

    pending_revenue = (
        Bill.objects
        .filter(payment_status='Pending')
        .aggregate(
            total=Sum('total_amount')
        )['total'] or 0
    )

    return render(
        request,
        'hotel_management/reports.html',
        {
            'total_bookings': total_bookings,
            'total_guests': total_guests,
            'total_rooms': total_rooms,
            'paid_revenue': paid_revenue,
            'room_revenue': room_revenue,
            'food_revenue': food_revenue,
            'pending_revenue': pending_revenue,
        }
    )