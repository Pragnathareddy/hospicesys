from django.contrib import admin

# Register your models here.
from .models import Doctor, Speciality, Education, TimeSlot,Clinic
from .models import DoctorSchedule, SocialMedia, Appointment, Invoice, Bill, Review, LikedReview, Reply
from .models import Patient, Prescription, MedicalRecord, Favourite



admin.site.register(Doctor)
admin.site.register(Patient)
admin.site.register(Clinic) 
