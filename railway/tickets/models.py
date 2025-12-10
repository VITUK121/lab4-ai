# tickets/models.py
from django.db import models
from django.forms import ValidationError
from datetime import date
from decimal import Decimal

class TicketOffice(models.Model):
    name = models.CharField(max_length=255, default="Залізнична каса Львів")
    location = models.CharField(max_length=255)
    phone = models.CharField(max_length=32)

    def __str__(self):
        return f"{self.name}, {self.location}, тел. {self.phone}"


class Person(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)

    class Meta:
        abstract = True

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def initials(self):
        return f"{self.first_name[0]}.{self.last_name[0]}."

    def greet(self):
        return f"Вітаю, я {self.full_name}!"


class Passenger(Person):
    passport = models.CharField(max_length=50)
    age = models.PositiveIntegerField()

    def passport_info(self):
        return f"Паспорт: {self.passport}"

    def age_group(self):
        if self.age < 18:
            return "неповнолітній"
        elif self.age > 60:
            return "пенсіонер"
        return "дорослий"

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.passport})"


class Cashier(Person):
    hire_date = models.DateField()

    def work_years(self):
        return date.today().year - self.hire_date.year

    def introduce(self):
        return f"Я касир {self.full_name}, працюю {self.work_years()} років."
    
    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class Trip(models.Model):
    start_station = models.CharField(max_length=255)
    end_station = models.CharField(max_length=255)
    distance_km = models.PositiveIntegerField()
    number = models.CharField(max_length=50)
    train_type = models.CharField(max_length=100)
    departure = models.DateTimeField()
    arrival = models.DateTimeField()
    
    # Виправлено: додано default, щоб старі записи не ламалися
    price = models.PositiveIntegerField(help_text="Вартість квитка:", default=100)
    capacity = models.PositiveIntegerField(default=100, help_text="Загальна кількість місць")

    @property
    def available_seats(self):
        sold_count = self.tickets.count() 
        return self.capacity - sold_count

    def duration_minutes(self):
        delta = self.arrival - self.departure
        return int(delta.total_seconds() // 60)

    def duration_str(self):
        mins = self.duration_minutes()
        hours = mins // 60
        minutes = mins % 60
        return f"{hours} год {minutes} хв"

    def __str__(self):
        return f"{self.start_station} — {self.end_station} ({self.distance_km} км)"


class Ticket(models.Model):
    TAX = Decimal('0.2')
    passenger = models.ForeignKey(Passenger, on_delete=models.CASCADE, related_name='tickets')
    cashier = models.ForeignKey(Cashier, on_delete=models.SET_NULL, null=True, related_name='sold_tickets')
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name='tickets')
    purchase_date = models.DateTimeField(auto_now_add=True)
    
    # ВИПРАВЛЕНО: base_price тепер число, а не ForeignKey
    # blank=True означає, що касиру не обов'язково вводити його вручну
    base_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True)
    
    payment_method = models.CharField(max_length=50, blank=True, null=True)
    paid_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    @staticmethod
    def calculate_discount(age):
        if age < 18:
            return 0.5
        elif age > 60:
            return 0.7
        return 1.0

    @staticmethod
    def calculate_discount(age):
        if age < 18:
            return Decimal('0.5') # Знижки теж Decimal
        elif age > 60:
            return Decimal('0.7')
        return Decimal('1.0')

    @property
    def price(self):
        # 1. Визначаємо базову ціну як Decimal
        if self.base_price:
            current_base = self.base_price # Це вже Decimal з бази
        else:
            current_base = Decimal(self.trip.price) # Конвертуємо int з Trip у Decimal
        
        # 2. Отримуємо знижку
        discount = self.calculate_discount(self.passenger.age)
        
        # 3. Рахуємо: Ціна * Знижка * (1 + Податок)
        # Всі компоненти тут Decimal, тому точність не втрачається
        raw_price = current_base * discount * (1 + self.TAX)
        
        # 4. Округляємо до 2 знаків
        return round(raw_price, 2)
    
    def clean(self):
        if self.pk is None:
            if self.trip.available_seats <= 0:
                raise ValidationError(f"На рейс {self.trip} більше немає вільних місць!")

    def save(self, *args, **kwargs):
        # Якщо base_price не задано - беремо з рейсу
        if not self.base_price:
            self.base_price = self.trip.price
        
        # Записуємо фінальну суму в paid_amount
        self.paid_amount = self.price
            
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.trip.id} {self.trip.start_station}-{self.trip.end_station}"