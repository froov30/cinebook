"""
Models module for the Movie Ticket Booking & Database Management System.

This module defines Python dataclasses representing the database tables with
robust serialization and deserialization capabilities.

Satisfies the following portfolio resume claims:
1. ★ "Eliminated double-bookings across all concurrent transactions through trigger-based seat allocation."
   - Dataclasses (like Booking and Seat) represent the schema structure which is protected
     at the database layer by BEFORE INSERT triggers to eliminate concurrent race conditions.
2. ★ "Enforced 3NF normalisation ensuring all updates propagate consistently with no manual correction needed."
   - The dataclasses strictly represent tables normalized to 3NF. They exclude transitive 
     fields (e.g. no movie_title in Show, no customer_name in Booking), preventing anomalies
     and ensuring single-point-of-update propagation.
3. ★ "Replaced ad-hoc reporting with stored procedures delivering occupancy and revenue analytics on demand."
   - Provides the precise data models mapping to the database tables queried by the 6 pre-compiled
     analytical stored procedures (e.g., occupancy reports, revenue breakdowns).
"""

from dataclasses import dataclass
from datetime import date, time, datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, Optional


# ==============================================================================
# HELPER PARSING FUNCTIONS
# ==============================================================================

def _parse_date(val: Any) -> Optional[date]:
    """
    Parses a date from string, datetime, or date objects.
    """
    if val is None:
        return None
    if isinstance(val, date):
        if isinstance(val, datetime):
            return val.date()
        return val
    if isinstance(val, str):
        return date.fromisoformat(val)
    raise TypeError(f"Cannot parse date from type {type(val)}: {val}")


def _parse_time(val: Any) -> Optional[time]:
    """
    Parses a time from string, timedelta, datetime, or time objects.
    """
    if val is None:
        return None
    if isinstance(val, time):
        return val
    if isinstance(val, timedelta):
        return (datetime.min + val).time()
    if isinstance(val, datetime):
        return val.time()
    if isinstance(val, str):
        return time.fromisoformat(val)
    raise TypeError(f"Cannot parse time from type {type(val)}: {val}")


def _parse_datetime(val: Any) -> Optional[datetime]:
    """
    Parses a datetime from string, date, or datetime objects.
    Normalizes UTC Z tags and space separators.
    """
    if val is None:
        return None
    if isinstance(val, datetime):
        return val
    if isinstance(val, date):
        return datetime.combine(val, time.min)
    if isinstance(val, str):
        normalized_str = val.replace(' ', 'T').replace('Z', '+00:00')
        return datetime.fromisoformat(normalized_str)
    raise TypeError(f"Cannot parse datetime from type {type(val)}: {val}")


def _parse_decimal(val: Any) -> Optional[Decimal]:
    """
    Parses a Decimal from string, float, integer, or Decimal objects.
    """
    if val is None:
        return None
    if isinstance(val, Decimal):
        return val
    return Decimal(str(val))


# ==============================================================================
# MODEL DATACLASSES
# ==============================================================================

@dataclass
class Movie:
    """
    Movie dataclass representing the Movies table.
    
    Claim 2 Link (3NF Normalization): Contains movie definitions only. Avoids
    redundancy in Shows by referencing movie_id as an FK.
    """
    title: str
    movie_id: Optional[int] = None
    genre: Optional[str] = None
    duration_min: Optional[int] = None
    language: Optional[str] = None
    release_date: Optional[date] = None
    rating: Optional[Decimal] = None

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> 'Movie':
        """
        Deserializes a dictionary into a Movie object.
        """
        return cls(
            title=str(d['title']),
            movie_id=int(d['movie_id']) if d.get('movie_id') is not None else None,
            genre=str(d['genre']) if d.get('genre') is not None else None,
            duration_min=int(d['duration_min']) if d.get('duration_min') is not None else None,
            language=str(d['language']) if d.get('language') is not None else None,
            release_date=_parse_date(d.get('release_date')),
            rating=_parse_decimal(d.get('rating'))
        )

    def to_dict(self) -> Dict[str, Any]:
        """
        Serializes a Movie object into a JSON-friendly dictionary.
        """
        return {
            'movie_id': self.movie_id,
            'title': self.title,
            'genre': self.genre,
            'duration_min': self.duration_min,
            'language': self.language,
            'release_date': self.release_date.isoformat() if self.release_date else None,
            'rating': float(self.rating) if self.rating else None
        }


@dataclass
class Cinema:
    """
    Cinema dataclass representing the Cinemas table.
    
    Claim 2 Link (3NF Normalization): Contains cinema details only. Prevents
    transitive dependencies (show_id -> cinema_id -> cinema_name) in the Shows table.
    """
    name: str
    cinema_id: Optional[int] = None
    location: Optional[str] = None
    city: Optional[str] = None
    total_halls: int = 1

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> 'Cinema':
        """
        Deserializes a dictionary into a Cinema object.
        """
        return cls(
            name=str(d['name']),
            cinema_id=int(d['cinema_id']) if d.get('cinema_id') is not None else None,
            location=str(d['location']) if d.get('location') is not None else None,
            city=str(d['city']) if d.get('city') is not None else None,
            total_halls=int(d.get('total_halls', 1))
        )

    def to_dict(self) -> Dict[str, Any]:
        """
        Serializes a Cinema object into a JSON-friendly dictionary.
        """
        return {
            'cinema_id': self.cinema_id,
            'name': self.name,
            'location': self.location,
            'city': self.city,
            'total_halls': self.total_halls
        }


@dataclass
class Show:
    """
    Show dataclass representing the Shows table.
    
    Claim 2 Link (3NF Normalization): Links Movies and Cinemas via foreign keys.
    Prevents transitive columns (e.g. movie_title) from polluting the show records.
    """
    movie_id: int
    cinema_id: int
    show_date: date
    show_time: time
    total_seats: int
    ticket_price: Decimal
    show_id: Optional[int] = None
    hall_number: Optional[str] = None
    status: str = 'SCHEDULED'

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> 'Show':
        """
        Deserializes a dictionary into a Show object.
        """
        return cls(
            movie_id=int(d['movie_id']),
            cinema_id=int(d['cinema_id']),
            show_date=_parse_date(d['show_date']),
            show_time=_parse_time(d['show_time']),
            total_seats=int(d['total_seats']),
            ticket_price=_parse_decimal(d['ticket_price']),
            show_id=int(d['show_id']) if d.get('show_id') is not None else None,
            hall_number=str(d['hall_number']) if d.get('hall_number') is not None else None,
            status=str(d.get('status', 'SCHEDULED'))
        )

    def to_dict(self) -> Dict[str, Any]:
        """
        Serializes a Show object into a JSON-friendly dictionary.
        """
        return {
            'show_id': self.show_id,
            'movie_id': self.movie_id,
            'cinema_id': self.cinema_id,
            'show_date': self.show_date.isoformat() if self.show_date else None,
            'show_time': self.show_time.isoformat() if self.show_time else None,
            'total_seats': self.total_seats,
            'ticket_price': float(self.ticket_price) if self.ticket_price else None,
            'hall_number': self.hall_number,
            'status': self.status
        }


@dataclass
class Seat:
    """
    Seat dataclass representing the Seats table.
    
    Claim 1 Link (Double-booking Prevention): Individual Seat entities are referenced
    by Bookings. The UNIQUE constraint (show_id, seat_number) combined with trigger allocation
    secures the integrity of concurrent bookings.
    """
    show_id: int
    seat_number: str
    seat_id: Optional[int] = None
    seat_type: str = 'Standard'
    price_modifier: Decimal = Decimal('1.00')

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> 'Seat':
        """
        Deserializes a dictionary into a Seat object.
        """
        return cls(
            show_id=int(d['show_id']),
            seat_number=str(d['seat_number']),
            seat_id=int(d['seat_id']) if d.get('seat_id') is not None else None,
            seat_type=str(d.get('seat_type', 'Standard')),
            price_modifier=_parse_decimal(d.get('price_modifier')) if d.get('price_modifier') is not None else Decimal('1.00')
        )

    def to_dict(self) -> Dict[str, Any]:
        """
        Serializes a Seat object into a JSON-friendly dictionary.
        """
        return {
            'seat_id': self.seat_id,
            'show_id': self.show_id,
            'seat_number': self.seat_number,
            'seat_type': self.seat_type,
            'price_modifier': float(self.price_modifier) if self.price_modifier else 1.00
        }


@dataclass
class Customer:
    """
    Customer dataclass representing the Customers table.
    
    Claim 2 Link (3NF Normalization): Keeps customer data isolated from booking transactions.
    """
    name: str
    email: str
    customer_id: Optional[int] = None
    phone: Optional[str] = None
    created_at: Optional[datetime] = None

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> 'Customer':
        """
        Deserializes a dictionary into a Customer object.
        """
        return cls(
            name=str(d['name']),
            email=str(d['email']),
            customer_id=int(d['customer_id']) if d.get('customer_id') is not None else None,
            phone=str(d['phone']) if d.get('phone') is not None else None,
            created_at=_parse_datetime(d.get('created_at'))
        )

    def to_dict(self) -> Dict[str, Any]:
        """
        Serializes a Customer object into a JSON-friendly dictionary.
        """
        return {
            'customer_id': self.customer_id,
            'name': self.name,
            'email': self.email,
            'phone': self.phone,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


@dataclass
class Booking:
    """
    Booking dataclass representing the Bookings table.
    
    Claim 1 Link (Double-booking Prevention): Protected by the prevent_double_booking
    BEFORE INSERT trigger, throwing SQLSTATE error if a confirmed duplicate is attempted.
    """
    seat_id: int
    customer_id: int
    amount: Decimal
    booking_id: Optional[int] = None
    booking_date: Optional[datetime] = None
    status: str = 'CONFIRMED'
    payment_ref: Optional[str] = None

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> 'Booking':
        """
        Deserializes a dictionary into a Booking object.
        """
        return cls(
            seat_id=int(d['seat_id']),
            customer_id=int(d['customer_id']),
            amount=_parse_decimal(d['amount']),
            booking_id=int(d['booking_id']) if d.get('booking_id') is not None else None,
            booking_date=_parse_datetime(d.get('booking_date')),
            status=str(d.get('status', 'CONFIRMED')),
            payment_ref=str(d['payment_ref']) if d.get('payment_ref') is not None else None
        )

    def to_dict(self) -> Dict[str, Any]:
        """
        Serializes a Booking object into a JSON-friendly dictionary.
        """
        return {
            'booking_id': self.booking_id,
            'seat_id': self.seat_id,
            'customer_id': self.customer_id,
            'booking_date': self.booking_date.isoformat() if self.booking_date else None,
            'amount': float(self.amount) if self.amount else None,
            'status': self.status,
            'payment_ref': self.payment_ref
        }


@dataclass
class BookingAudit:
    """
    BookingAudit dataclass representing the Booking_Audit table.
    
    Claim 1 Link (Double-booking Prevention): Works hand-in-hand with triggers
    (log_booking_insert, log_booking_cancel) that automatically append logs here on
    changes to Bookings.
    """
    audit_id: Optional[int] = None
    booking_id: Optional[int] = None
    action: Optional[str] = None
    action_time: Optional[datetime] = None
    performed_by: Optional[str] = None
    old_status: Optional[str] = None
    new_status: Optional[str] = None

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> 'BookingAudit':
        """
        Deserializes a dictionary into a BookingAudit object.
        """
        return cls(
            audit_id=int(d['audit_id']) if d.get('audit_id') is not None else None,
            booking_id=int(d['booking_id']) if d.get('booking_id') is not None else None,
            action=str(d['action']) if d.get('action') is not None else None,
            action_time=_parse_datetime(d.get('action_time')),
            performed_by=str(d['performed_by']) if d.get('performed_by') is not None else None,
            old_status=str(d['old_status']) if d.get('old_status') is not None else None,
            new_status=str(d['new_status']) if d.get('new_status') is not None else None
        )

    def to_dict(self) -> Dict[str, Any]:
        """
        Serializes a BookingAudit object into a JSON-friendly dictionary.
        """
        return {
            'audit_id': self.audit_id,
            'booking_id': self.booking_id,
            'action': self.action,
            'action_time': self.action_time.isoformat() if self.action_time else None,
            'performed_by': self.performed_by,
            'old_status': self.old_status,
            'new_status': self.new_status
        }
