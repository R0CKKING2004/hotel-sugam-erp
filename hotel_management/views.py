from datetime import datetime

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Sum

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

    return render(
        request,
        'hotel_management/login.html'
    )


def logout_view(request):

    logout(request)

    return redirect('login')


# =========================================================
# DASHBOARD
# PUBLIC - recruiter can view without login
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

    today = timezone.localdate()

    # =====================================================
    # TODAY'S ARRIVALS
    # =====================================================

    today_arrivals = Booking.objects.filter(
        check_in=today
    ).select_related(
        'guest',
        'room'
    )

    # =====================================================
    # TODAY'S DEPARTURES
    # =====================================================

    today_departures = Booking.objects.filter(
        check_out=today
    ).select_related(
        'guest',
        'room'
    )

    today_checkins = today_arrivals.count()

    today_checkouts = today_departures.count()

    # =====================================================
    # REVENUE
    # =====================================================

    paid_revenue = Bill.objects.filter(
        payment_status='Paid'
    ).aggregate(
        total=Sum('total_amount')
    )['total'] or 0

    pending_revenue = Bill.objects.filter(
        payment_status='Pending'
    ).aggregate(
        total=Sum('total_amount')
    )['total'] or 0

    room_revenue = Bill.objects.filter(
        payment_status='Paid'
    ).aggregate(
        total=Sum('room_charges')
    )['total'] or 0

    food_revenue = Bill.objects.filter(
        payment_status='Paid'
    ).aggregate(
        total=Sum('food_charges')
    )['total'] or 0

    pending_bills = Bill.objects.filter(
        payment_status='Pending'
    ).count()

    # =====================================================
    # OCCUPANCY
    # =====================================================

    if total_rooms > 0:

        occupancy_percentage = round(
            (occupied_rooms / total_rooms) * 100,
            2
        )

    else:

        occupancy_percentage = 0

    # =====================================================
    # RECENT BOOKINGS
    # =====================================================

    recent_bookings = Booking.objects.select_related(
        'guest',
        'room'
    ).order_by(
        '-id'
    )[:5]

    # =====================================================
    # RECENT FOOD ORDERS
    # =====================================================

    recent_food_orders = FoodOrder.objects.select_related(
        'food_item',
        'booking'
    ).order_by(
        '-order_date'
    )[:5]

    # =====================================================
    # PAID BILLS
    # =====================================================

    paid_bills = Bill.objects.select_related(
        'booking',
        'booking__guest'
    ).filter(
        payment_status='Paid'
    ).order_by(
        '-id'
    )[:5]

    # =====================================================
    # CONTEXT
    # =====================================================

    context = {

        'total_rooms': total_rooms,

        'available_rooms': available_rooms,

        'occupied_rooms': occupied_rooms,

        'maintenance_rooms': maintenance_rooms,

        'total_guests': total_guests,

        'total_bookings': total_bookings,

        # Numbers for dashboard cards
        'today_checkins': today_checkins,

        'today_checkouts': today_checkouts,

        # QuerySets for {% for %}
        'today_arrivals': today_arrivals,

        'today_departures': today_departures,

        'paid_revenue': paid_revenue,

        'pending_revenue': pending_revenue,

        'room_revenue': room_revenue,

        'food_revenue': food_revenue,

        'pending_bills': pending_bills,

        'occupancy_percentage': occupancy_percentage,

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
# ROOM MANAGEMENT
# =========================================================

def rooms(request):

    room_list = Room.objects.all().order_by(
        'room_number'
    )

    return render(
        request,
        'hotel_management/rooms.html',
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
        'hotel_management/add_room.html'
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
        'hotel_management/edit_room.html',
        {
            'room': room
        }
    )


# =========================================================
# GUEST MANAGEMENT
# =========================================================

def guests(request):

    guest_list = Guest.objects.all().order_by(
        '-id'
    )

    return render(
        request,
        'hotel_management/guests.html',
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
        'hotel_management/add_guest.html'
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
# BOOKING MANAGEMENT
# =========================================================

def bookings(request):

    booking_list = Booking.objects.select_related(
        'guest',
        'room'
    ).order_by(
        '-id'
    )

    total_bookings = booking_list.count()

    confirmed_bookings = booking_list.filter(
        status='Confirmed'
    ).count()

    checked_in = booking_list.filter(
        status='Checked In'
    ).count()

    checked_out = booking_list.filter(
        status='Checked Out'
    ).count()

    cancelled = booking_list.filter(
        status='Cancelled'
    ).count()

    context = {

        'bookings': booking_list,

        'total_bookings': total_bookings,

        'confirmed_bookings': confirmed_bookings,

        'checked_in': checked_in,

        'checked_out': checked_out,

        'cancelled': cancelled,
    }

    return render(
        request,
        'hotel_management/bookings.html',
        context
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

        try:

            check_in_date = datetime.strptime(
                check_in,
                '%Y-%m-%d'
            ).date()

            check_out_date = datetime.strptime(
                check_out,
                '%Y-%m-%d'
            ).date()

        except (TypeError, ValueError):

            messages.error(
                request,
                'Please enter valid dates.'
            )

            return redirect('add_booking')

        if check_out_date <= check_in_date:

            messages.error(
                request,
                'Check-out date must be after check-in date.'
            )

            return redirect('add_booking')

        overlapping_booking = Booking.objects.filter(
            room=room,
            status__in=[
                'Confirmed',
                'Checked In'
            ],
            check_in__lt=check_out_date,
            check_out__gt=check_in_date
        ).exists()

        if overlapping_booking:

            messages.error(
                request,
                'This room is already booked for the selected dates.'
            )

            return redirect('add_booking')

        Booking.objects.create(
            guest=guest,
            room=room,
            check_in=check_in_date,
            check_out=check_out_date,
            number_of_guests=number_of_guests,
            status='Confirmed'
        )

        messages.success(
            request,
            'Booking created successfully.'
        )

        return redirect('bookings')

    guests_list = Guest.objects.all().order_by(
        'name'
    )

    rooms_list = Room.objects.filter(
        status='Available'
    ).order_by(
        'room_number'
    )

    return render(
        request,
        'hotel_management/add_booking.html',
        {
            'guests': guests_list,
            'rooms': rooms_list
        }
    )


@login_required
def available_rooms(request):

    check_in = request.GET.get(
        'check_in'
    )

    check_out = request.GET.get(
        'check_out'
    )

    rooms_list = Room.objects.filter(
        status='Available'
    )

    if check_in and check_out:

        try:

            check_in_date = datetime.strptime(
                check_in,
                '%Y-%m-%d'
            ).date()

            check_out_date = datetime.strptime(
                check_out,
                '%Y-%m-%d'
            ).date()

            booked_room_ids = Booking.objects.filter(
                status__in=[
                    'Confirmed',
                    'Checked In'
                ],
                check_in__lt=check_out_date,
                check_out__gt=check_in_date
            ).values_list(
                'room_id',
                flat=True
            )

            rooms_list = rooms_list.exclude(
                id__in=booked_room_ids
            )

        except ValueError:
            pass

    data = [

        {
            'id': room.id,
            'room_number': room.room_number,
            'room_type': room.room_type,
            'price': str(room.price_per_night),
        }

        for room in rooms_list
    ]

    return JsonResponse(
        {
            'rooms': data
        }
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

        new_check_in = request.POST.get(
            'check_in'
        )

        new_check_out = request.POST.get(
            'check_out'
        )

        number_of_guests = request.POST.get(
            'number_of_guests'
        )

        status = request.POST.get(
            'status'
        )

        try:

            check_in_date = datetime.strptime(
                new_check_in,
                '%Y-%m-%d'
            ).date()

            check_out_date = datetime.strptime(
                new_check_out,
                '%Y-%m-%d'
            ).date()

        except (TypeError, ValueError):

            messages.error(
                request,
                'Please enter valid dates.'
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

        # Check overlap with other bookings
        overlapping_booking = Booking.objects.filter(
            room=booking.room,
            status__in=[
                'Confirmed',
                'Checked In'
            ],
            check_in__lt=check_out_date,
            check_out__gt=check_in_date
        ).exclude(
            id=booking.id
        ).exists()

        if overlapping_booking:

            messages.error(
                request,
                'This room is already booked for the selected dates.'
            )

            return redirect(
                'edit_booking',
                booking_id=booking.id
            )

        booking.check_in = check_in_date

        booking.check_out = check_out_date

        booking.number_of_guests = number_of_guests

        booking.status = status

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
        'hotel_management/edit_booking.html',
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
# RESTAURANT
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
        'hotel_management/restaurant.html',
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

        try:

            quantity = int(quantity)

            if quantity <= 0:

                raise ValueError

        except (TypeError, ValueError):

            messages.error(
                request,
                'Quantity must be a positive number.'
            )

            return redirect('restaurant')

        booking = None

        if booking_id:

            booking = Booking.objects.filter(
                id=booking_id
            ).first()

        FoodOrder.objects.create(
            booking=booking,
            food_item=food_item,
            quantity=quantity,
            status='Pending'
        )

        messages.success(
            request,
            'Food order added successfully.'
        )

    return redirect('restaurant')


# =========================================================
# FOOD ORDERS
# =========================================================

def food_orders(request):

    orders = FoodOrder.objects.select_related(
        'food_item',
        'booking',
        'booking__guest'
    ).order_by(
        '-order_date'
    )

    return render(
        request,
        'hotel_management/food_orders.html',
        {
            'food_orders': orders,
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

        status = request.POST.get(
            'status'
        )

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

def billing(request):

    bills = Bill.objects.select_related(
        'booking',
        'booking__guest',
        'booking__room'
    ).order_by(
        '-id'
    )

    total_bills = bills.count()

    paid_bills_count = bills.filter(
        payment_status='Paid'
    ).count()

    pending_bills_count = bills.filter(
        payment_status='Pending'
    ).count()

    total_revenue = bills.filter(
        payment_status='Paid'
    ).aggregate(
        total=Sum('total_amount')
    )['total'] or 0

    pending_amount = bills.filter(
        payment_status='Pending'
    ).aggregate(
        total=Sum('total_amount')
    )['total'] or 0

    context = {

        'bills': bills,

        'total_bills': total_bills,

        'paid_bills': paid_bills_count,

        'pending_bills': pending_bills_count,

        'total_revenue': total_revenue,

        'pending_amount': pending_amount,
    }

    return render(
        request,
        'hotel_management/billing.html',
        context
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

    nights = (
        booking.check_out -
        booking.check_in
    ).days

    if nights <= 0:
        nights = 1

    room_charges = (
        booking.room.price_per_night *
        nights
    )

    food_orders = FoodOrder.objects.filter(
        booking=booking,
        status='Completed'
    ).select_related(
        'food_item'
    )

    food_charges = sum(
        (
            order.food_item.price *
            order.quantity
            for order in food_orders
        ),
        0
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

        payment_method = request.POST.get(
            'payment_method'
        )

        valid_payment_methods = [
            'Cash',
            'Card',
            'UPI'
        ]

        if payment_method not in valid_payment_methods:

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


def invoice(request, bill_id):

    bill = get_object_or_404(
        Bill.objects.select_related(
            'booking',
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
# STAFF MANAGEMENT
# =========================================================

def staff(request):

    staff_list = Staff.objects.all().order_by(
        'name'
    )

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
        'hotel_management/add_staff.html'
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
        'Staff deleted successfully.'
    )

    return redirect('staff')


# =========================================================
# REPORTS
# =========================================================

def reports(request):

    total_rooms = Room.objects.count()

    available_rooms = Room.objects.filter(
        status='Available'
    ).count()

    occupied_rooms = Room.objects.filter(
        status='Occupied'
    ).count()

    total_guests = Guest.objects.count()

    total_bookings = Booking.objects.count()

    total_food_orders = FoodOrder.objects.count()

    total_staff = Staff.objects.count()

    # =====================================================
    # PAID REVENUE
    # =====================================================

    total_revenue = Bill.objects.filter(
        payment_status='Paid'
    ).aggregate(
        total=Sum('total_amount')
    )['total'] or 0

    # =====================================================
    # ROOM REVENUE
    # =====================================================

    room_revenue = Bill.objects.filter(
        payment_status='Paid'
    ).aggregate(
        total=Sum('room_charges')
    )['total'] or 0

    # =====================================================
    # FOOD REVENUE
    # =====================================================

    food_revenue = Bill.objects.filter(
        payment_status='Paid'
    ).aggregate(
        total=Sum('food_charges')
    )['total'] or 0

    # =====================================================
    # PENDING REVENUE
    # =====================================================

    pending_amount = Bill.objects.filter(
        payment_status='Pending'
    ).aggregate(
        total=Sum('total_amount')
    )['total'] or 0

    # =====================================================
    # REPORT CONTEXT
    # =====================================================

    context = {

        'total_rooms': total_rooms,

        'available_rooms': available_rooms,

        'occupied_rooms': occupied_rooms,

        'total_guests': total_guests,

        'total_bookings': total_bookings,

        'total_food_orders': total_food_orders,

        'total_staff': total_staff,

        'total_revenue': total_revenue,

        # IMPORTANT:
        # reports.html expects these names
        'paid_revenue': total_revenue,

        'pending_revenue': pending_amount,

        'room_revenue': room_revenue,

        'food_revenue': food_revenue,

        'pending_amount': pending_amount,
    }

    return render(
        request,
        'hotel_management/reports.html',
        context
    )