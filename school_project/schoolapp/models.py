from django.db import models
from django.contrib.auth.models import User
from phonenumber_field.modelfields import PhoneNumberField
from django.utils.translation import gettext_lazy as _
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status


class Department(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

class Classroom(models.Model):
    name = models.CharField(max_length=100)
    location = models.CharField(max_length=255, blank=True, null=True)
    capacity = models.PositiveIntegerField(blank=True, null=True)

    def __str__(self):
        return self.name

class Teacher(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='teacher_profile', null=True, blank=True)
    name = models.CharField(max_length=100)
    middle_name = models.CharField(max_length=100, blank=True, null=True)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = PhoneNumberField(_("Phone Number"), blank=True, null=True)
    specialization = models.CharField(max_length=100, blank=True)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)
    profile_photo = models.ImageField(upload_to='teacher_photos/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name}  {self.last_name}"


class Course(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    teacher = models.ForeignKey(Teacher, on_delete=models.SET_NULL, null=True, related_name='courses')
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)
    classroom = models.ForeignKey(Classroom, on_delete=models.SET_NULL, null=True, blank=True)
    # JSONField for schedule
    schedule = models.JSONField(help_text="e.g. {\"days\": [0, 2, 4], \"time\": \"10:00 - 11:30\"}")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_profile', null=True, blank=True)
    citizenship = models.CharField(max_length=32, blank=True, null=True)
    passport_number = models.CharField(max_length=9, blank=True, null=True)
    jshshir_code = models.CharField(max_length=14, blank=True, null=True)
    last_name = models.CharField(max_length=16, blank=True, null=True)
    name = models.CharField(max_length=16, blank=True, null=True)
    middle_name = models.CharField(max_length=16, blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
    ]
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, blank=True, null=True)

    NATIONALITY_CHOICES = [
        ('uzbek', 'Oʻzbek'),
        ('russian', 'Rus'),
        ('kazakh', 'Kazakh'),
        ('tajik', 'Tajik'),
        ('kyrgyz', 'Kyrgyz'),
        ('turkmen', 'Turkmen'),
        ('boshqa', 'Boshqa'),
    ]
    nationality = models.CharField(
        max_length=64,
        choices=NATIONALITY_CHOICES,
        blank=True,
        null=True
    )
    COUNTRY_CHOICES = [
        ('uzbekiston', "O'zbekiston"),
        ('rossiya', 'Rossiya'),
        ('qozogiston', 'Qozog\'iston'),
        ('tojikiston', 'Tojikiston'),
        ('qirgiziston', 'Qirg\'iziston'),
        ('turkmaniston', 'Turkmaniston'),
        ('boshqa', 'Boshqa'),
    ]
    country = models.CharField(
        max_length=64,
        choices=COUNTRY_CHOICES,
        blank=True,
        null=True
    )
    REGION_CHOICES = [
        ('andijon', 'Andijon'),
        ('buxoro', 'Buxoro'),
        ('fargona', 'Fargʻona'),
        ('jizzax', 'Jizzax'),
        ('xorazm', 'Xorazm'),
        ('namangan', 'Namangan'),
        ('navoiy', 'Navoiy'),
        ('qashqadaryo', 'Qashqadaryo'),
        ('qoraqalpogiston', 'Qoraqalpogʻiston Respublikasi'),
        ('samarqand', 'Samarqand'),
        ('sirdaryo', 'Sirdaryo'),
        ('surxondaryo', 'Surxondaryo'),
        ('toshkent', 'Toshkent'),
        ('toshkent_shahri', 'Toshkent shahri'),
    ]
    DISTRICT_CHOICES = {
        'andijon': [
            ('andijon_sh', 'Andijon shahri'),
            ('asaka', 'Asaka'),
            ('baliqchi', 'Baliqchi'),
            ('buloqboshi', 'Buloqboshi'),
            ('jalakuduk', 'Jalakuduk'),
            ('izboskan', 'Izboskan'),
            ('marhamat', 'Marhamat'),
            ('oltinko\'l', 'Oltinko\'l'),
            ('paxtaobod', 'Paxtaobod'),
            ('shahrixon', 'Shahrixon'),
            ('ulugnor', 'Ulug\'nor'),
            ('xonabod', 'Xonabod'),
            ('xojaobod', 'Xo\'jaobod'),
        ],
        'buxoro': [
            ('buxoro_sh', 'Buxoro shahri'),
            ('buxoro', 'Buxoro'),
            ('gijduvon', 'Gʻijduvon'),
            ('jondor', 'Jondor'),
            ('kogon', 'Kogon'),
            ('olot', 'Olot'),
            ('peshku', 'Peshku'),
            ('qorako\'l', 'Qorako\'l'),
            ('qorovulbozor', 'Qorovulbozor'),
            ('romitan', 'Romitan'),
            ('shafirkan', 'Shofirkon'),
            ('vobkent', 'Vobkent'),
        ],
        'fargona': [
            ('fargona_sh', 'Fargʻona shahri'),
            ('beshariq', 'Beshariq'),
            ('bogdod', 'Bogʻdod'),
            ('buvayda', 'Buvayda'),
            ('dangara', 'Dangʻara'),
            ('fargona', 'Fargʻona'),
            ('furqat', 'Furqat'),
            ('qo\'qon', 'Qoʻqon'),
            ('quva', 'Quva'),
            ('quvasoy', 'Quvasoy'),
            ('rishton', 'Rishton'),
            ('sox', 'Soʻx'),
            ('toshloq', 'Toshloq'),
            ('uchko\'prik', 'Uchkoʻprik'),
            ('oltiariq', 'Oltiariq'),
            ('yozyovon', 'Yozyovon'),
            ('ush', 'Ush'),
            ('margilon', 'Margʻilon'),
        ],
        'jizzax': [
            ('jizzax_sh', 'Jizzax shahri'),
            ('arnasoy', 'Arnasoy'),
            ('baxmal', 'Baxmal'),
            ('do\'stlik', 'Doʻstlik'),
            ('forish', 'Forish'),
            ('gallaorol', 'Gʻallaorol'),
            ('sharof_rashidov', 'Sharof Rashidov'),
            ('mirzacho\'l', 'Mirzachoʻl'),
            ('paxtakor', 'Paxtakor'),
            ('yangiobod', 'Yangiobod'),
            ('zarbdor', 'Zarbdor'),
            ('zomin', 'Zomin'),
            ('zafarobod', 'Zafarobod'),
        ],
        'xorazm': [
            ('urganch_sh', 'Urganch shahri'),
            ('urganch', 'Urganch'),
            ('xiva', 'Xiva'),
            ('xazorasp', 'Xazorasp'),
            ('xonqa', 'Xonqa'),
            ('yangiariq', 'Yangiariq'),
            ('yangibozor', 'Yangibozor'),
            ('shovot', 'Shovot'),
            ('hazorasp', 'Hazorasp'),
            ('qoshkopir', 'Qoʻshkoʻpir'),
            ('gurlan', 'Gurlan'),
            ('bogot', 'Bogʻot'),
            ('tuproqqala', 'Tuproqqalʼa'),
        ],
        'namangan': [
            ('namangan_sh', 'Namangan shahri'),
            ('chortoq', 'Chortoq'),
            ('chust', 'Chust'),
            ('kosonsoy', 'Kosonsoy'),
            ('mingbuloq', 'Mingbuloq'),
            ('namangan', 'Namangan'),
            ('norin', 'Norin'),
            ('pop', 'Pop'),
            ('to\'raqo\'rg\'on', 'Toʻraqoʻrgʻon'),
            ('uchqo\'rg\'on', 'Uchqoʻrgʻon'),
            ('uychi', 'Uychi'),
            ('yangiqo\'rg\'on', 'Yangiqoʻrgʻon'),
            ('davlatobod', 'Davlatobod'),
        ],
        'navoiy': [
            ('navoiy_sh', 'Navoiy shahri'),
            ('konimex', 'Konimex'),
            ('karmana', 'Karmana'),
            ('navbahor', 'Navbahor'),
            ('nurota', 'Nurota'),
            ('qiziltepa', 'Qiziltepa'),
            ('tomdi', 'Tomdi'),
            ('uchquduq', 'Uchquduq'),
            ('xatirchi', 'Xatirchi'),
            ('zarafshon', 'Zarafshon'),
        ],
        'qashqadaryo': [
            ('qarshi_sh', 'Qarshi shahri'),
            ('chiroqchi', 'Chiroqchi'),
            ('dehqonobod', 'Dehqonobod'),
            ('guzor', 'Gʻuzor'),
            ('kasbi', 'Kasbi'),
            ('kitob', 'Kitob'),
            ('koson', 'Koson'),
            ('mirishkor', 'Mirishkor'),
            ('muborak', 'Muborak'),
            ('nishon', 'Nishon'),
            ('qamashi', 'Qamashi'),
            ('qarshi', 'Qarshi'),
            ('shahrisabz', 'Shahrisabz'),
            ('yakkabog\'', 'Yakkabogʻ'),
        ],
        'qoraqalpogiston': [
            ('nukus_sh', 'Nukus shahri'),
            ('amudaryo', 'Amudaryo'),
            ('beruniy', 'Beruniy'),
            ('chimboy', 'Chimboy'),
            ('ellikqala', 'Ellikqala'),
            ('kegeyli', 'Kegeyli'),
            ('mo\'ynoq', 'Moʻynoq'),
            ('nukus', 'Nukus'),
            ('qonliko\'l', 'Qonlikoʻl'),
            ('qorao\'zak', 'Qoraoʻzak'),
            ('shumanay', 'Shumanay'),
            ('taxtako\'pir', 'Taxtakoʻpir'),
            ('to\'rtko\'l', 'Toʻrtkoʻl'),
            ('xojeli', 'Xojeli'),
            ('qangli', 'Qangli'),
        ],
        'samarqand': [
            ('samarqand_sh', 'Samarqand shahri'),
            ('bulungur', 'Bulungʻur'),
            ('ishtixon', 'Ishtixon'),
            ('jomboy', 'Jomboy'),
            ('kattaqorgon', 'Kattaqoʻrgʻon'),
            ('narpay', 'Narpay'),
            ('nurobod', 'Nurobod'),
            ('oqdaryo', 'Oqdaryo'),
            ('paxtachi', 'Paxtachi'),
            ('payariq', 'Payariq'),
            ('pastdargom', 'Pastdargʻom'),
            ('samarqand', 'Samarqand'),
            ('toyloq', 'Toyloq'),
            ('urgut', 'Urgut'),
        ],
        'sirdaryo': [
            ('guliston_sh', 'Guliston shahri'),
            ('boyovut', 'Boyovut'),
            ('guliston', 'Guliston'),
            ('mirzaobod', 'Mirzaobod'),
            ('oqoltin', 'Oqoltin'),
            ('sardoba', 'Sardoba'),
            ('sayxunobod', 'Sayxunobod'),
            ('shirin', 'Shirin'),
            ('sirdaryo', 'Sirdaryo'),
            ('xovos', 'Xovos'),
            ('yangiyer', 'Yangiyer'),
        ],
        'surxondaryo': [
            ('termiz_sh', 'Termiz shahri'),
            ('angor', 'Angor'),
            ('boysun', 'Boysun'),
            ('denov', 'Denov'),
            ('jarqo\'rg\'on', 'Jarqoʻrgʻon'),
            ('muzrabot', 'Muzrabot'),
            ('oqoltin', 'Oltinsoy'),
            ('qiziriq', 'Qiziriq'),
            ('sariosiyo', 'Sariosiyo'),
            ('sherobod', 'Sherobod'),
            ('shurchi', 'Shoʻrchi'),
            ('termiz', 'Termiz'),
            ('uzun', 'Uzun'),
        ],
        'toshkent': [
            ('bekobod', 'Bekobod'),
            ('bostanliq', 'Boʻstonliq'),
            ('buka', 'Boʻka'),
            ('chinoz', 'Chinoz'),
            ('chirchiq', 'Chirchiq'),
            ('yangiyo\'l', 'Yangiyoʻl'),
            ('ohangaron', 'Ohangaron'),
            ('olmaliq', 'Olmaliq'),
            ('parkent', 'Parkent'),
            ('piskent', 'Piskent'),
            ('quyichirchiq', 'Quyi Chirchiq'),
            ('oqqo\'rg\'on', 'Oqqoʻrgʻon'),
            ('orik', 'Oʻrta Chirchiq'),
            ('toshkent', 'Toshkent'),
            ('zangiota', 'Zangiota'),
            ('yukorichirchiq', 'Yuqori Chirchiq'),
        ],
        'toshkent_shahri': [
            ('bektemir', 'Bektemir'),
            ('mirzo_ulugbek', 'Mirzo Ulugʻbek'),
            ('mirobod', 'Mirobod'),
            ('olmazor', 'Olmazor'),
            ('sergeli', 'Sergeli'),
            ('shayxontohur', 'Shayxontohur'),
            ('uchtepa', 'Uchtepa'),
            ('chilonzor', 'Chilonzor'),
            ('yakkasaroy', 'Yakkasaroy'),
            ('yangihayot', 'Yangihayot'),
            ('yashnobod', 'Yashnobod'),
            ('yunusobod', 'Yunusobod'),
        ],
    }
    region = models.CharField(
        max_length=64,
        choices=REGION_CHOICES,
        blank=True,
        null=True
    )   
    district = models.CharField(max_length=64, blank=True, null=True)
    address = models.CharField(max_length=256, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    specialization = models.CharField(max_length=128, blank=True, null=True)
    faculty = models.CharField(max_length=128, blank=True, null=True)
    course_year = models.CharField(max_length=32, blank=True, null=True)
    payment_type = models.CharField(max_length=64, blank=True, null=True)
    education_type = models.CharField(max_length=64, blank=True, null=True)
    education_form = models.CharField(max_length=64, blank=True, null=True)
    study_year = models.CharField(max_length=32, blank=True, null=True)
    semester = models.CharField(max_length=32, blank=True, null=True)
    profile_photo = models.ImageField(upload_to='student_photos/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} {self.last_name}"


class Enrollment(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='enrollments')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments')

    class Meta:
        unique_together = ('student', 'course')

    def __str__(self):
        return f"{self.student} in {self.course}"

class Task(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    file = models.FileField(upload_to='tasks/', blank=True, null=True)
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='tasks')
    course = models.ForeignKey(Course, on_delete=models.SET_NULL, null=True, blank=True)
    max_score = models.IntegerField(default=100)
    
    due_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.title}"

class TaskSubmission(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='submissions')
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='submissions')
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='submissions')
    submitted_file = models.FileField(upload_to='submissions/', blank=True, null=True)
    submitted_text = models.TextField(blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    is_done = models.BooleanField(default=False)
    score = models.IntegerField(blank=True, null=True)
    feedback = models.TextField(blank=True, null=True)  
    

    class Meta:
        unique_together = ('task', 'student')

    def __str__(self):
        return f"Submission: {self.student.name} → {self.task.title}"
