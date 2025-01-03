from django import forms
from django.forms import ModelForm

from .models import Doctor, Education, SocialMedia
from .models import Patient, Prescription, MedicalRecord

# Doctors Forms

class DoctorForm(ModelForm):
	class Meta:
		model = Doctor
		fields = ('user', 'image', 'first_name', 'second_name', 'title', 'd_o_b', 'gender', 'biography', 
			'phone_no', 'email', 'address_line1', 'address_line2', 'country', 'county', 'town', 'pricing', 
			'services', 'specialization', 'clinic', 'clinic_address', 'speciality','drclinic')

class EducationForm(ModelForm):
	class Meta:
		model = Education
		fields = ('doctor', 'degree', 'institute', 'y_o_c')

 
class SocialMediaForm(ModelForm):
	
	class Meta:
		model = SocialMedia
		fields = ('doctor', 'facebook_url', 'twitter_url', 'instagram_url', 'pinterest_url', 'linkedin_url', 
			'youtube_url')


# Patients Forms

class PrescriptionForm(ModelForm):

	class Meta:
		model = Prescription
		fields = ( 'patient', 'doctor', 'name', 'quantity', 'days', 'morning', 'afternoon', 'evening', 'night')


class PatientForm(ModelForm):
	class Meta:
		model = Patient
		fields = ('user', 'image', 'first_name', 'second_name', 'd_o_b', 'gender', 'blood_group', 'phone_no', 
			'email', 'street_lane', 'country', 'county', 'town')
        


class MedicalRecordForm(ModelForm):
	class Meta:
		model = MedicalRecord
		fields = ('patient', 'doctor', 'date_recorded', 'description', 'attachment')
