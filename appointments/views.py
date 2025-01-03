from django.shortcuts import render, redirect

from django.http import HttpResponse, JsonResponse, HttpResponseRedirect
from django.contrib.auth import authenticate, logout, login
from django.contrib.auth.models import User, Group, Permission
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils import timezone

from .forms import DoctorForm, EducationForm
from .forms import SocialMediaForm, PrescriptionForm, PatientForm, MedicalRecordForm
from .models import Clinic, Doctor, Speciality, Education,  TimeSlot
from .models import DoctorSchedule, SocialMedia, Appointment, Invoice, Bill, Review, LikedReview, Reply
from .models import Patient, Prescription, MedicalRecord, Favourite
from django.shortcuts import get_list_or_404, get_object_or_404
 

import datetime as dt
from easy_pdf.rendering import render_to_pdf_response
# Create your views here.

def doctor_register(request):
	if request.is_ajax():
		user = User.objects.create_user(request.POST['email'], request.POST['email'], 
			request.POST['password'])
		if user.is_active:
			user.first_name = request.POST['first_name']
			user.save()
			try:
				doc_group = Group.objects.get(name="doctors_group")
				user.groups.add(doc_group)
			except Exception:
				doc_group = Group.objects.create(name='doctors_group')
				perm_doc_add = Permission.objects.get(codename='add_doctor')
				perm_doc_del = Permission.objects.get(codename='delete_doctor')
				perm_doc_chg = Permission.objects.get(codename='change_doctor')
				doc_group.permissions.add(perm_doc_add, perm_doc_chg, perm_doc_del)
				user.groups.add(doc_group)
			return JsonResponse({"success": "User " + request.POST['first_name'] +" Created.", 
					"redirect": "../../login/"}, status=200)
		else:
			return JsonResponse({"error": "Error Creating User " + request.POST['first_name'] +"."}, 
				status=200) 
	else:
		return render(request, 'doctors/doctor-register.html')


def check_doctor(user):
	group = user.groups.get()
	return group.name=='doctors_group'


def check_settings(user):
	profile = Doctor.objects.filter(user=user.id)
	return profile.count()>=1


@login_required(login_url='/login/')
@user_passes_test(check_doctor, login_url='/login/')
def doctor_profile_settings(request):
	if request.method == 'POST':
		if int(request.POST['user']) == request.user.id:
			try:
				a = Doctor.objects.get(user=request.user.id)
				f = DoctorForm(request.POST, request.FILES, instance=a)
				f.save()
				user=request.user
				user.last_name = request.POST['second_name']
				user.first_name = request.POST['first_name']
				user.email = request.POST['email']
				user.save()
				return HttpResponseRedirect('../profile/settings-page2/')
			except Exception:
				form = DoctorForm(request.POST, request.FILES)
				if form.is_valid():
					form.save()
					user=request.user
					user.last_name = request.POST['second_name']
					user.first_name = request.POST['first_name']
					user.email = request.POST['email']
					user.save()
					return HttpResponseRedirect('../profile/settings-page2/')
				else:
					return HttpResponse(form.errors)
					# return render(request, 'appointments/profile-settings.html', {'form': form})
		else:
			return HttpResponse("form.errors")
	else:
		profile = None
		form = None
		try:
			profile = Doctor.objects.get(user=request.user.id)
			form = DoctorForm(instance=profile)
		except Exception:
			form = DoctorForm()
		specialities = Speciality.objects.all()
		clinics = Clinic.objects.all()
		return render(request, 'doctors/doctor-profile-settings.html', {'specialities': specialities, 
			'profile': profile, 'form': form,'clinics':clinics})


@login_required(login_url='/login/')
@user_passes_test(check_doctor, login_url='/login/')
@user_passes_test(check_settings, login_url='/doctors/profile-settings/')
def doctor_profile_page2(request):
	profile = Doctor.objects.get(user=request.user.id)
	edu = Education.objects.filter(doctor=profile.id)
 
	if request.method == 'POST':
		#Education
		for a in edu:
			data = {"doctor": profile.id, "degree": request.POST['degree'+str(a.id)], 
			"institute": request.POST['institute'+str(a.id)], "y_o_c": request.POST['y_o_c'+str(a.id)]}
			form = EducationForm(data, instance=a)
			if form.is_valid():
				form.save()

		form_num = int(request.POST['edu_form-num'])
		for x in range(0,form_num):
			x = str(x)
			try:
				data = {"doctor": profile.id, "degree": request.POST['degree-'+x], 
				"institute": request.POST['institute-'+x], "y_o_c": request.POST['y_o_c-'+x]}
				form = EducationForm(data)
				if form.is_valid():
					form.save()
			except Exception:
				pass

		

		return HttpResponseRedirect('../../../doctors/')
	else:
		return render(request, 'doctors/doctor-profile-page2.html', {'profile': profile, 'education': edu})


@login_required(login_url='/login/')
@user_passes_test(check_doctor, login_url='/login/')
@user_passes_test(check_settings, login_url='/doctors/profile-settings/')
def doctor_dashboard(request):
	profile = Doctor.objects.get(user=request.user.id)
	appointments = Appointment.objects.filter(doctor=profile.id)
	upcoming_appointments = appointments.filter(booking_date__gte=dt.date.today())
	today_appointments = appointments.filter(status='ACCEPTED', booking_date__date=dt.date.today())
	my_patients = []
	for appointment in appointments:
		if appointment.patient not in my_patients:
			my_patients += [appointment.patient]
	return render(request, 'doctors/doctor-dashboard.html', {"profile": profile, "appointments": appointments,
		"upcoming_appointments": upcoming_appointments, "today_appointments": today_appointments, 
		"total_patients": len(my_patients)})


@login_required(login_url='/login/')
@user_passes_test(check_doctor, login_url='/login/')
@user_passes_test(check_settings, login_url='/doctors/profile-settings/')
def appointments(request):
	profile = Doctor.objects.get(user=request.user.id)
	appointments = Appointment.objects.filter(doctor=profile.id)
	return render(request, 'doctors/appointments.html', {'profile' :profile, 'appointments': appointments})


@login_required(login_url='/login/')
@user_passes_test(check_doctor, login_url='/login/')
@user_passes_test(check_settings, login_url='/doctors/profile-settings/')
def appointment_accept(request, slug, appointment_id):
	doctor = Doctor.objects.get(user=request.user.id)
	appointment = Appointment.objects.get(id=appointment_id)
	if appointment.doctor.id == doctor.id:
		appointment.status = 'ACCEPTED'
		appointment.save()
		return JsonResponse({"success": "Appointment ACCEPTED.", "redirect": "../../../../doctors/"}, 
			status=200)
	else:
		return JsonResponse({"error": "Error Updating Appointment"}, status=200) 


@login_required(login_url='/login/')
@user_passes_test(check_doctor, login_url='/login/')
@user_passes_test(check_settings, login_url='/doctors/profile-settings/')
def appointment_cancel(request, slug, appointment_id):
	doctor = Doctor.objects.get(user=request.user.id)
	appointment = Appointment.objects.get(id=appointment_id)
	if appointment.doctor.id == doctor.id:
		appointment.status = 'CANCELLED'
		appointment.save()
		return JsonResponse({"success": "Appointment CANCELLED.", "redirect": "../../../../doctors/"}, 
			status=200)
	else:
		return JsonResponse({"error": "Error Updating Appointment"}, status=200) 


@login_required(login_url='/login/')
@user_passes_test(check_doctor, login_url='/login/')
@user_passes_test(check_settings, login_url='/doctors/profile-settings/')
def appointment_complete(request, slug, appointment_id):
	doctor = Doctor.objects.get(user=request.user.id)
	appointment = Appointment.objects.get(id=appointment_id)
	if appointment.doctor.id == doctor.id:
 
		appointment.status = 'COMPLETED'
		appointment.save()
		p = appointment.patient
		url = "../../../../doctors/patient-profile/"+p.first_name+"-"+p.second_name+"/"+str(p.id)+"/"
		return JsonResponse({"success": "Appointment COMPLETED.", "redirect": url}, status=200)
 
	else:
		return JsonResponse({"error": "Error Updating Appointment"}, status=200) 


@login_required(login_url='/login/')
@user_passes_test(check_doctor, login_url='/login/')
@user_passes_test(check_settings, login_url='/doctors/profile-settings/')
def my_patients(request):
	profile = Doctor.objects.get(user=request.user.id)
	appointments = Appointment.objects.filter(doctor=profile.id).exclude(status='CANCELLED')
	patients = []
	for appointment in appointments:
		if appointment.patient not in patients:
			patients += [appointment.patient]

	return render(request, 'doctors/my-patients.html', {'profile' :profile, 'patients': patients})


@login_required(login_url='/login/')
@user_passes_test(check_doctor, login_url='/login/')
@user_passes_test(check_settings, login_url='/doctors/profile-settings/')
def schedule_timings(request):
	profile = Doctor.objects.get(user=request.user.id)
	schedules = DoctorSchedule.objects.filter(doctor=profile.id)
	if schedules.count() < 7:
		res = new_schedule(profile)
		if res:
			schedules = DoctorSchedule.objects.filter(doctor=profile.id)
		else:
			return HttpResponse(res)

	hours = {}
	for i in range(0, 24):
		time = dt.time(i,00,00)
		time1 = dt.time(i,30,00)
		hours.setdefault(f"{time:%H:%M:%S}", f"{time:%I.%M %p}")
		hours.setdefault(f"{time1:%H:%M:%S}", f"{time1:%I.%M %p}")
	return render(request, 'doctors/schedule-timings.html', {'profile': profile, 'schedules': schedules, 
		"hours": hours})


@login_required(login_url='/login/')
@user_passes_test(check_doctor, login_url='/login/')
@user_passes_test(check_settings, login_url='/doctors/profile-settings/')
def new_timeslot(request):
	if request.method == 'POST':
		form_num = int(request.POST['add_form-num'])
		for x in range(0, form_num):
			if not request.POST['start_time_'+str(x)] == '' and not request.POST['end_time_'+str(x)] == '':
				schedule_id = int(request.POST['schedule']) 
				start =	request.POST['start_time_'+str(x)] 
				end = request.POST['end_time_'+str(x)]
				schedule = DoctorSchedule.objects.get(id=schedule_id)
				time_slot = TimeSlot(schedule=schedule, start_time=start, end_time=end)
				time_slot.save()

		redirect = '../schedule-timings/'	
		return JsonResponse({"success": "Time Slots Created.", "redirect": redirect}, status=200)
	else:
		return HttpResponseRedirect('../schedule-timings/')


@login_required(login_url='/login/')
@user_passes_test(check_doctor, login_url='/login/')
@user_passes_test(check_settings, login_url='/doctors/profile-settings/')
def update_timeslot(request):
	if request.method == 'POST':
		form_num = int(request.POST['edit_form-num'])
		schedule_id = int(request.POST['schedule'])
		schedule = DoctorSchedule.objects.get(id=schedule_id)
		time_slots = TimeSlot.objects.filter(schedule=schedule.id)
		for slot in time_slots:
			s = str(slot.id)
			if not request.POST['start_time'+s] == '' and not request.POST['end_time'+s] == '':
				slot.start_time = request.POST['start_time'+s]
				slot.end_time = request.POST['end_time'+s]
				slot.save()

		if form_num > 0:
			for x in range(0, form_num):
				if not request.POST['start_time_'+str(x)] == '' and not request.POST['end_time_'+str(x)] == '': 
					start =	request.POST['start_time_'+str(x)] 
					end = request.POST['end_time_'+str(x)]
					time_slot = TimeSlot(schedule=schedule, start_time=start, end_time=end)
					time_slot.save()

		redirect = '../schedule-timings/'	
		return JsonResponse({"success": "Time Slots Created.", "redirect": redirect}, status=200)
	else:
		return HttpResponseRedirect('../../schedule-timings/')


@login_required(login_url='/login/')
@user_passes_test(check_doctor, login_url='/login/')
@user_passes_test(check_settings, login_url='/doctors/profile-settings/')
def delete_timeslot(request, slug, slot_id):
	t_slots = TimeSlot.objects.get(id=slot_id)
	schdl = t_slots.schedule
	if schdl.doctor.user == request.user:
		t_slots.delete()
	return HttpResponseRedirect('../../../../schedule-timings/')


@login_required(login_url='/login/')
@user_passes_test(check_doctor, login_url='/login/')
@user_passes_test(check_settings, login_url='/doctors/profile-settings/')
def invoices(request):
	doctor = Doctor.objects.get(user=request.user.id)
	invoices = Invoice.objects.filter(doctor=doctor.id)
	return render(request, 'doctors/invoices.html', {'profile': doctor, 'invoices': invoices})


@login_required(login_url='/login/')
def invoice(request, slug, invoice_id):
	inv_id = int(invoice_id)
	invoice = Invoice.objects.get(id=inv_id)
	access = False
	profile = None
	try:
		group = request.user.groups.get()
		if group.name=='patients_group':
			profile = Patient.objects.get(user=request.user.id)
			if profile.id == invoice.patient.id:
				access = True
		elif group.name=='doctors_group':
			profile = Doctor.objects.get(user=request.user.id)
			if profile.id == invoice.doctor.id:
				access = True
		elif request.user.is_superuser:
			access = True
	except Exception:
		if request.user.is_superuser:
			profile = Doctor.objects.get(user=request.user.id)
			access = True
		else:
			access = False
	if access:
		bills = Bill.objects.filter(invoice=invoice.id)
		return render(request, 'patients/invoice-view.html', {'invoice': invoice, 'bills': bills, 
			'profile': profile})


@login_required(login_url='/login/')
def invoice_pdf(request, slug, invoice_id):
	inv_id = int(invoice_id)
	invoice = Invoice.objects.get(id=inv_id)
	group = request.user.groups.get()
	access = False
	profile = None
	try:
		if group.name=='patients_group':
			profile = Patient.objects.get(user=request.user.id)
			if profile.id == invoice.patient.id:
				access = True
		elif group.name=='doctors_group':
			profile = Doctor.objects.get(user=request.user.id)
			if profile.id == invoice.doctor.id:
				access = True
		elif user.is_superuser():
			access = True
	except Exception:
		access = False

	if access:
		bills = Bill.objects.filter(invoice=invoice.id)
		return render_to_pdf_response(request, 'cas/invoice-pdf.html', {'invoice': invoice, 
			'bills': bills, 'request': request})


@login_required(login_url='/login/')
@user_passes_test(check_doctor, login_url='/login/')
@user_passes_test(check_settings, login_url='/doctors/profile-settings/')
def reviews(request):
	doctor = Doctor.objects.get(user=request.user.id)
	reviews = Review.objects.filter(appointment__doctor=doctor.id)
	return render(request, 'doctors/reviews.html', {'profile': doctor, 'reviews': reviews})


@login_required(login_url='/login/')
def like_review(request, review_id):
	if request.is_ajax():
		liked = LikedReview.objects.filter(user=request.user.id, review=review_id)
		review = Review.objects.get(id=review_id)
		if liked.count() == 0:
			like = LikedReview(review=review, user=request.user, recommend=True)
			like.save()
			redirect = '../../../doctor-profile/doctor-name/'+str(review.appointment.doctor.id)+'/'
			return JsonResponse({"success": "Review Liked.", "redirect": redirect}, status=200)
		else:
			liked = LikedReview.objects.get(user=request.user.id, review=review_id)
			if not liked.recommend:
				liked.recommend = True
				liked.save()
				redirect = '../../../doctor-profile/doctor-name/'+str(review.appointment.doctor.id)+'/'
				return JsonResponse({"success": "Review Liked.", "redirect": redirect}, status=200)
			else:
				return JsonResponse({"error": "Review Liked."}, status=200)
	else:
		return HttpResponseRedirect('../../../doctor-profile/doctor-name/'+str(review.appointment.doctor.id)+'/')



@login_required(login_url='/login/')
def dislike_review(request, review_id):
	if request.is_ajax():
		liked = LikedReview.objects.filter(user=request.user.id, review=review_id)
		review = Review.objects.get(id=review_id)
		if liked.count() == 0:
			like = LikedReview(review=review, user=request.user, recommend=False)
			like.save()
			redirect = '../../../doctor-profile/doctor-name/'+str(review.appointment.doctor.id)+'/'
			return JsonResponse({"success": "Review Disliked.", "redirect": redirect}, status=200)
		else:
			liked = LikedReview.objects.get(user=request.user.id, review=review_id)
			if liked.recommend:
				liked.recommend = False
				liked.save()
				redirect = '../../../doctor-profile/doctor-name/'+str(review.appointment.doctor.id)+'/'
				return JsonResponse({"success": "Review Disliked.", "redirect": redirect}, status=200)
			else:
				return JsonResponse({"error": "Review Disliked."}, status=200)
	else:
		return HttpResponseRedirect('../../../doctor-profile/doctor-name/'+str(review.appointment.doctor.id)+'/')


@login_required(login_url='/login/')
def reply_review(request):
	if request.is_ajax():
		review = Review.objects.get(id=int(request.POST['review']))
		reply = Reply(review=review, user=request.user, text=request.POST['text'])
		reply.save()
		return JsonResponse({"success": "Posted.", "redirect": request.POST['next']}, status=200)
	else:
		return redirect(request.path_info)

@login_required(login_url='/login/')
@user_passes_test(check_doctor, login_url='/login/')
@user_passes_test(check_settings, login_url='/doctors/profile-settings/')
def social_media(request):
	doctor = Doctor.objects.get(user=request.user.id)
	if request.method == 'POST':
		try:
			social = SocialMedia.objects.get(doctor=doctor.id)
			form = SocialMediaForm(request.POST, instance=social)
			if form.is_valid():
				form.save()
		except Exception:
			form = SocialMediaForm(request.POST)
			if form.is_valid():
				form.save()
		redirect = '../social-media/'	
		return JsonResponse({"success": "Social Sites Updated.", "redirect": redirect}, status=200)
	else:
		social = None
		try:
			social = SocialMedia.objects.get(doctor=doctor.id)
		except Exception:
			social = None
		return render(request, 'doctors/social-media.html', {'profile': doctor, 'social': social})


@login_required(login_url='/login/')
@user_passes_test(check_doctor, login_url='/login/')
@user_passes_test(check_settings, login_url='/doctors/profile-settings/')
def doctor_change_password(request):
	doctor = Doctor.objects.get(user=request.user.id)
	if request.is_ajax():
		usr = request.user
		if usr.check_password(request.POST['old_pswd']):
			if request.POST['new_pswd'] == request.POST['cfm_pswd']:
				if not request.POST['new_pswd'] == request.POST['old_pswd']:
					usr.set_password(request.POST['new_pswd'])
					usr.save()
					logout(request)
					redirect = '../../login/'
					return JsonResponse({"success": "Social Sites Updated.", "redirect": redirect}, status=200)
				else:
					return JsonResponse({"error": "The Password Has not Changed"}, status=200)
			else:
				return JsonResponse({"error": "Confirm and New Password don't Match"}, status=200)
		else:
			return JsonResponse({"error": "Incorrect password"}, status=200)
	else:
		return render(request, 'doctors/doctor-change-password.html', {'profile': doctor})


@login_required(login_url='/login/')
@user_passes_test(check_doctor, login_url='/login/')
@user_passes_test(check_settings, login_url='/doctors/profile-settings/')
def patient_profile(request, slug, patient_id):
	doctor = Doctor.objects.get(user=request.user.id)
	patient = Patient.objects.get(id=patient_id)
	appointments = Appointment.objects.filter(patient=patient_id, doctor=doctor.id)
	prescriptions = Prescription.objects.filter(patient=patient_id) 
	records = MedicalRecord.objects.filter(patient=patient_id) 
	invoices = Invoice.objects.filter(patient=patient_id, doctor=doctor.id)
	return render(request, 'doctors/patient-profile.html', {'profile': doctor, 'patient': patient, 
		'last_appointments': appointments, 'prescriptions': prescriptions, 'records': records, 
		'invoices': invoices})


@login_required(login_url='/login/')
@user_passes_test(check_doctor, login_url='/login/')
@user_passes_test(check_settings, login_url='/doctors/profile-settings/')
def add_prescription(request, slug, patient_id):
	doctor = Doctor.objects.get(user=request.user.id)
	patient = Patient.objects.get(id=patient_id)
	if request.method == 'POST':
		form_num = int(request.POST['form-num'])
		for x in range(0,form_num):
			x = str(x)
			#try:
			morning = None 
			afternoon = None 
			evening = None 
			night = None
			try:
				if request.POST['morning_'+x] == 'on':
					morning = True
			except Exception:
				morning = False

			try:
				if request.POST['afternoon_'+x] == 'on':
					afternoon = True
			except Exception:
				afternoon = False

			try:
				if request.POST['evening_'+x] == 'on':
					evening = True
			except Exception:
				evening = False

			try:
				if request.POST['night_'+x] == 'on':
					night = True
			except Exception:
				night = False
			#patient, doctor, name, quantity, days, 

			data = {"patient": patient_id, "doctor": doctor.id, "name": request.POST['name_'+x], 
			"quantity": request.POST['quantity_'+x], "days": request.POST['days_'+x], 
			"morning": morning, "afternoon": afternoon, "evening": evening, "night": night}
			form = PrescriptionForm(data)
			if form.is_valid():
				form.save()
			#except Exception:
			#	pass
		return HttpResponseRedirect('../../../patient-profile/'+slug+'/'+str(patient_id)+'/')
	else:
		return render(request, 'doctors/add-prescription.html', {'profile': doctor, 'patient': patient})


@login_required(login_url='/login/')
@user_passes_test(check_doctor, login_url='/login/')
@user_passes_test(check_settings, login_url='/doctors/profile-settings/')
def edit_prescription(request, patient_id, slug, prescription_id):
	doctor = Doctor.objects.get(user=request.user.id)
	patient = Patient.objects.get(id=patient_id)
	prescription = Prescription.objects.get(id=prescription_id)
	if patient_id == prescription.patient.id:
		if request.method == 'POST':
			form = PrescriptionForm(request.POST, instance=prescription)
			if form.is_valid():
				form.save()
			else:
				return HttpResponse(form.errors)
			prescription = Prescription.objects.get(id=prescription_id)
			return HttpResponseRedirect('../../../../patient-profile/'+patient.first_name+'-'+patient.second_name+'/'+str(patient.id)+'/')
	return render(request, 'doctors/edit-prescription.html', {'profile': doctor, 'patient': patient,
		'prescription': prescription})


@login_required(login_url='/login/')
def prescription_pdf(request, slug, prescription_id):
	prescription = Prescription.objects.get(id=prescription_id)
	group = request.user.groups.get()
	access = False
	profile = None
	try:
		if group.name=='patients_group':
			profile = Patient.objects.get(user=request.user.id)
			if profile.id == prescription.patient.id:
				access = True
		elif group.name=='doctors_group':
			profile = Doctor.objects.get(user=request.user.id)
			if profile.id == prescription.doctor.id:
				access = True
		elif user.is_superuser():
			access = True
	except Exception:
		access = False

	if access:
		return render_to_pdf_response(request, 'doctors/prescription-pdf.html', 
			{'prescription': prescription})


@login_required(login_url='/login/')
@user_passes_test(check_doctor, login_url='/login/')
@user_passes_test(check_settings, login_url='/doctors/profile-settings/')
def delete_prescription(request, slug, prescription_id):
	prescription = Prescription.objects.get(id=prescription_id)
	doctor = Doctor.objects.get(user=request.user.id)
	if doctor.id == prescription.doctor.id:
		prescription.delete()
		redirect = '../../../patient-profile/'+prescription.patient.first_name+'-'+prescription.patient.second_name+'/'+str(prescription.patient.id)+'/'
		return JsonResponse({"success": "Prescription Removed.", "redirect": redirect}, status=200)


@login_required(login_url='/login/')
@user_passes_test(check_doctor, login_url='/login/')
@user_passes_test(check_settings, login_url='/doctors/profile-settings/')
def add_medical_record(request, slug, patient_id):
	if request.method == 'POST':
		doctor = Doctor.objects.get(user=request.user.id)
		# patient, doctor, date_recorded, description, attachment
		if doctor.id == int(request.POST['doctor']) and patient_id == int(request.POST['doctor']):
			form = MedicalRecordForm(request.POST, request.FILES)
			if form.is_valid():
				form.save()
			else:
				return HttpResponse(form.errors)
	
	return HttpResponseRedirect('../../../patient-profile/'+slug+'/'+str(patient_id)+'/')


@login_required(login_url='/login/')
@user_passes_test(check_doctor, login_url='/login/')
@user_passes_test(check_settings, login_url='/doctors/profile-settings/')
def edit_medical_record(request, patient_id, slug, mr_id):
	doctor = Doctor.objects.get(user=request.user.id)
	patient = Patient.objects.get(id=patient_id)
	mr = MedicalRecord.objects.get(id=mr_id)
	if request.method == 'POST':
		if patient_id == mr.patient.id and doctor.id == mr.doctor.id:
			form = MedicalRecordForm(request.POST, request.FILES, instance=mr)
			if form.is_valid():
				form.save()
				return HttpResponseRedirect('../../../../patient-profile/'+slug+'/'+str(patient_id)+'/')
			else:
				return HttpResponse(form.errors)
	form = MedicalRecordForm(instance=mr)
	return render(request, 'doctors/edit-medical-record.html', {'profile': doctor, 'patient': patient,
		'record': mr, 'form': form})


@login_required(login_url='/login/')
@user_passes_test(check_doctor, login_url='/login/')
@user_passes_test(check_settings, login_url='/doctors/profile-settings/')
def delete_medical_record(request, slug, mr_id):
	mr = MedicalRecord.objects.get(id=mr_id)
	doctor = Doctor.objects.get(user=request.user.id)
	if doctor.id == mr.doctor.id:
		mr.delete()
		redirect = '../../../patient-profile/'+mr.patient.first_name+'-'+mr.patient.second_name+'/'+str(mr.patient.id)+'/'
		return JsonResponse({"success": "Medical Record Removed.", "redirect": redirect}, status=200)


@login_required(login_url='/login/')
@user_passes_test(check_doctor, login_url='/login/')
@user_passes_test(check_settings, login_url='/doctors/profile-settings/')
def add_billing(request, slug, patient_id, appointment_id):
	doctor = Doctor.objects.get(user=request.user.id)
	patient = Patient.objects.get(id=patient_id)
	appointment = Appointment.objects.get(id=appointment_id, patient=patient_id, doctor=doctor.id)
	if request.method == 'POST':
		form_num = int(request.POST['form-num'])
		total_amount = 0
		for x in range(0,form_num):
			x = str(x)
			total_amount += float(request.POST['amount_'+x])
		#Create Invoice
		invoice = Invoice(patient=patient, doctor=doctor, total_amount=total_amount)
		invoice.save()
		# Create Bills
		for x in range(0,form_num):
			x = str(x)
			bill = Bill(invoice=invoice, appointment=appointment, description=request.POST['title_'+x], 
				quantity=1.0, vat=0.0, amount=float(request.POST['amount_'+x]), paid=True)
			bill.save()
		return HttpResponseRedirect('../../../../patient_profile/'+slug+'/'+str(patient_id)+'/')
	else:
		return render(request, 'doctors/add-billing.html', {'profile': doctor, 'patient': patient})


@login_required(login_url='/login/')
@user_passes_test(check_doctor, login_url='/login/')
@user_passes_test(check_settings, login_url='/doctors/profile-settings/')
def edit_billing(request, patient_id, slug, inv_id):
	doctor = Doctor.objects.get(user=request.user.id)
	patient = Patient.objects.get(id=patient_id)
	invoice = Invoice.objects.get(id=inv_id)
	return render(request, 'doctors/edit-billing.html', {'profile': doctor, 'patient': patient, 
		'invoice': invoice})


@login_required(login_url='/login/')
@user_passes_test(check_doctor, login_url='/login/')
 
def new_schedule(doctor):
	days = ['sunday', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday']
	err = []
	for day in days:
		data = DoctorSchedule(doctor = doctor, day = day, interval = 30)
		data.save()
		
	return True



# # # # Patients Views here.


def register(request):
	if request.is_ajax():
		user = User.objects.create_user(request.POST['email'], request.POST['email'], 
			request.POST['password'])
		if user.is_active:
			user.first_name = request.POST['first_name']
			user.save()
			try:
				pt_group = Group.objects.get(name="patients_group")
				user.groups.add(pt_group)
			except Exception:
				pt_group = Group.objects.create(name='patients_group')
				perm_pt_add = Permission.objects.get(codename='add_patient')
				perm_pt_del = Permission.objects.get(codename='delete_patient')
				perm_pt_chg = Permission.objects.get(codename='change_patient')
				pt_group.permissions.add(perm_pt_add, perm_pt_chg, perm_pt_del)
				user.groups.add(pt_group)
			return JsonResponse({"success": "User " + request.POST['first_name'] +" Created.", 
				"redirect": "../../login/"}, status=200)
		else:
			return JsonResponse({"error": "Error Creating User " + request.POST['first_name'] +"."}, 
				status=200) 
	else:
		return render(request, 'patients/register.html')


def check_patient(user):
	group = user.groups.get()
	return group.name == 'patients_group'


def check_settings(user):
	profile = Patient.objects.filter(user=user.id)
	return profile.count()>=1


@login_required(login_url='/login/')
@user_passes_test(check_patient, login_url='/login/')
@user_passes_test(check_settings, login_url='/patients/profile-settings/')
def patient_dashboard(request):
	profile = Patient.objects.get(user=request.user.id)
	appointments = Appointment.objects.filter(patient=profile.id)
	prescriptions = Prescription.objects.filter(patient=profile.id) 
	medical_records = MedicalRecord.objects.filter(patient=profile.id)
	invoices = Invoice.objects.filter(patient=profile.id)
	return render(request, 'patients/patient-dashboard.html', {"profile": profile, "appointments": appointments, 
		'prescriptions': prescriptions, 'medical_records': medical_records, 'invoices': invoices})


@login_required(login_url='/login/')
@user_passes_test(check_patient, login_url='/login/')
def profile_settings(request):
	#data = {'user': request.user.id, 'first_name': request.user.first_name, 'email': request.user.email}
	if request.method == 'POST':
		if int(request.POST['user']) == request.user.id:
			try:
				a = Patient.objects.get(user=request.user.id)
				f = PatientForm(request.POST, request.FILES, instance=a)
				f.save()
				return HttpResponseRedirect('../../patients/')
			except Exception:
				form = PatientForm(request.POST, request.FILES)
				if form.is_valid():
					form.save()
					user=request.user
					user.last_name = request.POST['second_name']
					user.first_name = request.POST['first_name']
					user.email = request.POST['email']
					user.save()
					return HttpResponseRedirect('../../patients/')
				else:
					return HttpResponse(form.errors)
					# return render(request, 'appointments/profile-settings.html', {'form': form})
		else:
			return HttpResponse("form.errors")
	else:
		profile = None
		form = None
		try:
			profile = Patient.objects.get(user=request.user.id)
			form = PatientForm(instance=profile)
		except Exception:
			profile = request.user
			form = PatientForm()
		return render(request, 'patients/profile-settings.html', {"profile": profile, "form": form})


def get_profile(user):
	if user.is_authenticated:
		profile = None
		try:
			group = user.groups.get()
			if group.name=='patients_group':
				profile = Patient.objects.get(user=user.id)
			elif group.name=='doctors_group':
				profile = Doctor.objects.get(user=user.id)
			elif user.is_superuser:
				profile = Doctor.objects.get(user=user.id)
			else:
				return profile
			return profile
		except Exception:
			if user.is_superuser:
				profile = Doctor.objects.get(user=user.id)
			return profile
	else:
		return None


def doctor_profile(request, slug, doctor_id):
	doctor = Doctor.objects.get(id=doctor_id)
	edu = Education.objects.filter(doctor=doctor_id) 
	reviews = Review.objects.filter(appointment__doctor=doctor_id)
	schedule = DoctorSchedule.objects.filter(doctor=doctor_id)
	profile = get_profile(request.user)
	return render(request, 'patients/doctor-profile.html', {"doctor": doctor, "education": edu, "profile": profile, 
		"reviews": reviews, "schedule": schedule})

from django.shortcuts import render
from django.core.serializers.json import DjangoJSONEncoder
import json
from .models import Appointment, Doctor

@login_required(login_url='/login/')
@user_passes_test(check_patient, login_url='/login/')
@user_passes_test(check_settings, login_url='/patients/profile-settings/')

def booking(request, slug, doctor_id):

	doctor = get_object_or_404(Doctor, id=doctor_id)
	print(f"[DEBUG] Doctor fetched: {doctor.full_name()} (ID: {doctor_id})")

    # Fetch the weekly schedule for the doctor
	weekly_schedule = DoctorSchedule.objects.filter(doctor=doctor)
	schedule_data = {}

	for schedule in weekly_schedule:
		time_slots = TimeSlot.objects.filter(schedule=schedule).order_by('start_time')
		slot_list = [
            {
                "start_time": slot.start_time.strftime('%H:%M'),
                "end_time": slot.end_time.strftime('%H:%M')
            }
            for slot in time_slots
        ]
		schedule_data[schedule.day] = {
            "interval": schedule.interval,
            "slots": slot_list
        }
		print(f"[DEBUG] Schedule for {schedule.day}: {schedule_data[schedule.day]}")

    # Fetch all booked appointments for the doctor
	today = dt.date.today()
	booked_appointments = Appointment.objects.filter(
        doctor=doctor, booking_date__date__gte=today
    ).values('booking_date')
	booked_data = {}

	for appointment in booked_appointments:
		appointment_date = appointment['booking_date'].date().strftime('%Y-%m-%d')
		appointment_time = appointment['booking_date'].time().strftime('%H:%M')

		if appointment_date not in booked_data:
			booked_data[appointment_date] = []
		booked_data[appointment_date].append(appointment_time)
    
	print(f"[DEBUG] Booked appointments: {booked_data}")

    # Serialize data for the frontend
	schedule_json = json.dumps(schedule_data, cls=DjangoJSONEncoder)
	booked_json = json.dumps(booked_data, cls=DjangoJSONEncoder)

	return render(request, 'patients/booking.html', {
        "doctor": doctor,
        "weekly_schedule": schedule_json,
        "booked_appointments": booked_json,
    })

@login_required(login_url='/login/')
@user_passes_test(check_patient, login_url='/login/')
@user_passes_test(check_settings, login_url='/patients/profile-settings/')
def checkout222(request):
	if request.method == 'POST':
		doctor_id = int(request.POST['doctor'])
		doctor = Doctor.objects.get(id = doctor_id)
		# 12:00:00_17/03/2021
		time_date = str(request.POST['time_date']).split('_')
		time = time_date[0].split(':')
		date = time_date[1].split('/')
		book_date = dt.datetime(int(date[2]), int(date[1]), int(date[0]), int(time[0]), int(time[1], 0))
		profile = ""
		try:
			profile = Patient.objects.get(user = request.user.id)
		except Exception:
			profile = {}

		booking_fee = 100.0
		video_call = 50.0
		consultation_fee = doctor.pricing
		total_fee = booking_fee + video_call + consultation_fee
		
		return render(request, 'patients/checkout.html', {'book_date': book_date, 'doctor': doctor, 
			'profile': profile, 'booking_fee': booking_fee, 'video_call': video_call, 'total_fee': total_fee})
	else:
		pass


@login_required(login_url='/login/')
@user_passes_test(check_patient, login_url='/login/')
@user_passes_test(check_settings, login_url='/patients/profile-settings/')
def booking_success222(request):
	if request.method == 'POST':
		doctor_id = int(request.POST['doctor'])
		doctor = Doctor.objects.get(id = doctor_id)
		profile = ""
		try:
			profile = Patient.objects.get(user = request.user.id)
		except Exception:
			profile = {}

		booking_fee = 100.0
		video_call = 50.0
		consultation_fee = doctor.pricing
		total_fee = booking_fee + video_call + consultation_fee
		# Save the new Appointment to DB
		appointment = Appointment(doctor=doctor, patient=profile, purpose='General', category='General', 
			amount=total_fee, status='WAIT', booking_date=request.POST['date'])
		appointment.save()
		#Create Invoice
		invoice = Invoice(patient=profile, doctor=doctor, total_amount=total_fee)
		invoice.save()
		# Create Bills
		booking = Bill(invoice=invoice, appointment=appointment, description="Booking Fee", quantity=1.0, 
			vat=0.0, amount=booking_fee, paid=True)
		booking.save()
		video = Bill(invoice=invoice, appointment=appointment, description="Video Call Fee", quantity=1.0, 
			vat=0.0, amount=video_call, paid=True)
		video.save()
		consultation = Bill(invoice=invoice, appointment=appointment, description="Consultation Fee", 
			quantity=1.0, vat=0.0, amount=consultation_fee, paid=True)
		consultation.save()
		return render(request, 'patients/booking-success.html', {'appointment': appointment, 'invoice': invoice, 
			'profile': profile})
	else:
		pass


@login_required(login_url='/login/')
@user_passes_test(check_patient, login_url='/login/')
@user_passes_test(check_settings, login_url='/patients/profile-settings/')
def checkout(request):
	if request.method == 'POST':
		doctor_id = int(request.POST['doctor'])
		doctor = Doctor.objects.get(id = doctor_id)
		# 12:00:00_17/03/2021
		time_date = str(request.POST['time_date']).split('_')
		time = time_date[0].split(':')
		date = time_date[1].split('/')
		book_date = dt.datetime(int(date[2]), int(date[1]), int(date[0]), int(time[0]), int(time[1], 0))
		profile = ""
		try:
			profile = Patient.objects.get(user = request.user.id)
		except Exception:
			profile = {}

		booking_fee = 100.0
		video_call = 50.0
		consultation_fee = doctor.pricing
		total_fee = booking_fee + video_call + consultation_fee
  
  
		if  Appointment.objects.filter(doctor=doctor,booking_date=book_date ).exists():
      
			return JsonResponse({"error": "Please select a different Date and Time to book. This has already been scheduled."}, status=200) 	
   
  
		# Save the new Appointment to DB
		appointment = Appointment(doctor=doctor, patient=profile, purpose='General', category='General', 
			amount=total_fee, status='WAIT', booking_date=book_date)
		appointment.save()
		#Create Invoice
		invoice = Invoice(patient=profile, doctor=doctor, total_amount=total_fee)
		invoice.save()
		# Create Bills
		booking = Bill(invoice=invoice, appointment=appointment, description="Booking Fee", quantity=1.0, 
			vat=0.0, amount=booking_fee, paid=True)
		booking.save()
		video = Bill(invoice=invoice, appointment=appointment, description="Video Call Fee", quantity=1.0, 
			vat=0.0, amount=video_call, paid=True)
		video.save()
		consultation = Bill(invoice=invoice, appointment=appointment, description="Consultation Fee", 
			quantity=1.0, vat=0.0, amount=consultation_fee, paid=True)
		consultation.save()
		return render(request, 'patients/booking-success.html', {'appointment': appointment, 'invoice': invoice, 
			'profile': profile})
	else:
		pass


@login_required(login_url='/login/')
@user_passes_test(check_patient, login_url='/login/')
@user_passes_test(check_settings, login_url='/patients/profile-settings/')
def booking_success(request):
	if request.method == 'POST':
		doctor_id = int(request.POST['doctor'])
		doctor = Doctor.objects.get(id = doctor_id)
		profile = ""
		try:
			profile = Patient.objects.get(user = request.user.id)
		except Exception:
			profile = {}

		booking_fee = 100.0
		video_call = 50.0
		consultation_fee = doctor.pricing
		total_fee = booking_fee + video_call + consultation_fee
		# Save the new Appointment to DB
		appointment = Appointment(doctor=doctor, patient=profile, purpose='General', category='General', 
			amount=total_fee, status='WAIT', booking_date=request.POST['date'])
		appointment.save()
		#Create Invoice
		invoice = Invoice(patient=profile, doctor=doctor, total_amount=total_fee)
		invoice.save()
		# Create Bills
		booking = Bill(invoice=invoice, appointment=appointment, description="Booking Fee", quantity=1.0, 
			vat=0.0, amount=booking_fee, paid=True)
		booking.save()
		video = Bill(invoice=invoice, appointment=appointment, description="Video Call Fee", quantity=1.0, 
			vat=0.0, amount=video_call, paid=True)
		video.save()
		consultation = Bill(invoice=invoice, appointment=appointment, description="Consultation Fee", 
			quantity=1.0, vat=0.0, amount=consultation_fee, paid=True)
		consultation.save()
		return render(request, 'patients/booking-success.html', {'appointment': appointment, 'invoice': invoice, 
			'profile': profile})
	else:
		pass


@login_required(login_url='/login/')
@user_passes_test(check_patient, login_url='/login/')
@user_passes_test(check_settings, login_url='/patients/profile-settings/')
def invoice_view(request, slug, invoice_id):
	inv_id = int(invoice_id)
	invoice = Invoice.objects.get(id=inv_id)
	bills = Bill.objects.filter(invoice=invoice.id)
	profile = Patient.objects.get(user = request.user.id)
	return render(request, 'patients/invoice-view.html', {'invoice': invoice, 'bills': bills, 
		'profile': profile})


@login_required(login_url='/login/')
@user_passes_test(check_patient, login_url='/login/')
@user_passes_test(check_settings, login_url='/patients/profile-settings/')
def favourites(request):
	profile = Patient.objects.get(user = request.user.id)
	favourites = Favourite.objects.filter(patient = profile.id)
	return render(request, 'patients/favourites.html', {'profile': profile, 'favourites': favourites})


@login_required(login_url='/login/')
@user_passes_test(check_patient, login_url='/login/')
@user_passes_test(check_settings, login_url='/patients/profile-settings/')
def favourite_doctor(request, slug, doctor_id):
	patient = Patient.objects.get(user=request.user.id)
	favourites = Favourite.objects.filter(doctor=doctor_id, patient=patient.id)
	if request.is_ajax():
		if not favourites.count()==0:
			favourite = favourites[0]
			favourite.delete()
			return JsonResponse({"responseJSON": "Removed from Favourite"}, status=200)
		else:
			doctor = Doctor.objects.get(id=doctor_id)
			favourite = Favourite(doctor=doctor, patient=patient)
			favourite.save()
			return JsonResponse({"responseJSON": "Added to Favourite"}, status=200)
	else:		
		if not count==0:
			favourite = favourites[0]
			favourite.delete()
		else:
			doctor = Doctor.objects.get(id=doctor_id)
			favourite = Favourite(doctor=doctor, patient=patient)
			favourite.save()
		return HttpResponseRedirect('../../favourites/')


@login_required(login_url='/login/')
@user_passes_test(check_patient, login_url='/login/')
def add_review(request):
	patient = Patient.objects.get(user=request.user.id)
	if request.is_ajax():
		rate = int(request.POST['rating'])
		recommend = bool(request.POST['recommend'])
		text = request.POST['text']
		patient = Patient.objects.get(user=request.user.id)
		appointment = patient.last_appointment()
		review = Review(appointment = appointment, rate=rate, recommend=recommend, text=text)
		review.save()
		redirect = '../../doctor-profile/doctor-name/'+str(appointment.doctor.id)+'/'
		return JsonResponse({"success": "Doctor Reviewed.", "redirect": redirect}, status=200)
	else:
		return HttpResponseRedirect('../../doctor-profile/doctor-name/'+str(appointment.doctor.id)+'/')


@login_required(login_url='/login/')
@user_passes_test(check_patient, login_url='/login/')
def change_password(request):
	patient = Patient.objects.get(user=request.user.id)
	if request.is_ajax():
		usr = request.user
		if usr.check_password(request.POST['old_password']):
			if request.POST['new_password'] == request.POST['confirm_password']:
				if not request.POST['new_password'] == request.POST['old_password']:
					usr.set_password(request.POST['new_password'])
					usr.save()
					logout(request)
					redirect = '../../login/'
					return JsonResponse({"success": "Password Updated.", "redirect": redirect}, status=200)
				else:
					return JsonResponse({"error": "The Password Has not Changed"}, status=200)
			else:
				return JsonResponse({"error": "Confirm and New Password don't Match"}, status=200)
		else:
			return JsonResponse({"error": "Incorrect password"}, status=200)
	else:
		return render(request, 'patients/change-password.html', {'profile': patient})



@login_required(login_url='/login/')
@user_passes_test(check_patient, login_url='/login/')
@user_passes_test(check_settings, login_url='/patients/profile-settings/')
def chat(request):
	patient = Patient.objects.get(user=request.user.id)
	return render(request, 'patients/chat.html', {'profile': patient})

import json

import json
from datetime import datetime
from django.utils.timezone import make_aware

from django.core.mail import send_mail

@login_required(login_url='/login/')
@user_passes_test(check_patient, login_url='/login/')
@user_passes_test(check_settings, login_url='/patients/profile-settings/')
def checkoutt(request):
    if request.method == 'POST':
        try:
            # Debug: Print the raw request body
            print(f"[DEBUG] Full request body: {request.body}")

            # Parse JSON payload
            try:
                data = json.loads(request.body)
                print(f"[DEBUG] Parsed JSON data: {data}")
            except json.JSONDecodeError as e:
                print(f"[ERROR] Failed to decode JSON: {str(e)}")
                return JsonResponse({"error": "Invalid JSON data."}, status=400)

            # Fetch doctor details from parsed JSON
            doctor_id = data.get('doctor')
            if not doctor_id:
                print("[ERROR] Doctor ID is missing from the JSON data.")
                return JsonResponse({"error": "Doctor ID is missing from the request."}, status=400)

            # Convert doctor_id to integer
            doctor_id = int(doctor_id)
            doctor = get_object_or_404(Doctor, id=doctor_id)

            # Parse the time and date from JSON
            time_date = data.get('time_date')
            if not time_date:
                print("[ERROR] Time and date are missing from the JSON data.")
                return JsonResponse({"error": "Time and date are missing from the request."}, status=400)

            # Parse time_date using datetime.strptime
            try:
                booking_date = datetime.strptime(time_date, "%I:%M %p_%Y-%m-%d")
                booking_date = make_aware(booking_date)  # Ensure timezone awareness
            except ValueError as e:
                print(f"[ERROR] Invalid time_date format: {time_date}. Exception: {str(e)}")
                return JsonResponse({"error": "Invalid time or date format in the request."}, status=400)

            # Fetch the patient's profile
            profile = get_object_or_404(Patient, user=request.user)

            # Define fees
            booking_fee = 100.0
            video_call_fee = 50.0
            consultation_fee = doctor.pricing
            total_fee = booking_fee + video_call_fee + consultation_fee

            # Check if the slot is already booked
            if Appointment.objects.filter(doctor=doctor, booking_date=booking_date).exists():
                print(f"[ERROR] Time slot already booked for doctor {doctor_id} at {booking_date}.")
                return JsonResponse({"error": "This time slot is already booked. Please select a different date and time."}, status=400)


 

            # Save the new Appointment to the database
            appointment = Appointment(
                doctor=doctor,
                patient=profile,
                purpose='General',
                category='General',
                amount=total_fee,
                status='WAIT',
                booking_date=booking_date
            )
            appointment.save()

            # Create Invoice
            invoice = Invoice(
                patient=profile,
                doctor=doctor,
                total_amount=total_fee
            )
            invoice.save()

            # Create Bills
            Bill.objects.create(
                invoice=invoice,
                appointment=appointment,
                description="Booking Fee",
                quantity=1.0,
                vat=0.0,
                amount=booking_fee,
                paid=True
            )
            Bill.objects.create(
                invoice=invoice,
                appointment=appointment,
                description="Video Call Fee",
                quantity=1.0,
                vat=0.0,
                amount=video_call_fee,
                paid=True
            )
            Bill.objects.create(
                invoice=invoice,
                appointment=appointment,
                description="Consultation Fee",
                quantity=1.0,
                vat=0.0,
                amount=consultation_fee,
                paid=True
            )

            # Redirect to the patient's dashboard
            redirect_url = '/patients'
            success_message = "Appointment booked successfully!"


            print(f"[SUCCESS] Appointment booked successfully for doctor {doctor_id} at {booking_date}.")
            return JsonResponse({"success": success_message, "redirect": redirect_url}, status=200)
        except Exception as e:
            print(f"[ERROR] Exception occurred: {str(e)}")
            return JsonResponse({"error": f"An error occurred: {str(e)}"}, status=500)
    else:
        print("[INFO] Non-POST request received.")
        return render(request, 'patients/booking-notification.html')
