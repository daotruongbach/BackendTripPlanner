# apps/accounts/models.py
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone

AGE_CHILD_MAX = 5              # <6
AGE_STUDENT_MAX = 22           # <=22 (tức <23)
AGE_SENIOR_MIN_EXCLUSIVE = 60  # >60

class UserManager(BaseUserManager):
    use_in_migrations = True
    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError("Email is required")
        email = self.normalize_email(email)
        user = self.model(email=email, username=email, **extra_fields)
        if password: user.set_password(password)
        else: user.set_unusable_password()
        user.save(using=self._db)
        return user
    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)
    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")
        return self._create_user(email, password, **extra_fields)

class CustomerType(models.IntegerChoices):
    CHILD = 1, "Trẻ em (<6)"
    STUDENT = 2, "HSSV (<23)"
    ADULT = 3, "Người lớn"
    SENIOR = 4, "Người già (>60)"

class User(AbstractUser):
    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=150, blank=True)
    last_name  = models.CharField(max_length=150, blank=True)

    date_of_birth = models.DateField(null=True, blank=True, help_text="YYYY-MM-DD")
    is_student    = models.BooleanField(default=False, help_text="Đánh dấu nếu là học sinh/sinh viên thực sự")
    customer_type = models.PositiveSmallIntegerField(
        choices=CustomerType.choices, null=True, blank=True,
        help_text="Nếu bỏ trống sẽ tự gợi ý theo ngày sinh + is_student",
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []
    objects = UserManager()

    class Meta:
        indexes = [models.Index(fields=["customer_type"])]

    def __str__(self): return self.email

    @property
    def age(self):
        if not self.date_of_birth:
            return None
        today = timezone.localdate()
        dob = self.date_of_birth
        years = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
        return max(years, 0)

    def suggest_customer_type(self):
        a = self.age
        if a is None: return None
        if a <= AGE_CHILD_MAX: return CustomerType.CHILD
        if a <= AGE_STUDENT_MAX: return CustomerType.STUDENT if self.is_student else CustomerType.ADULT
        if a > AGE_SENIOR_MIN_EXCLUSIVE: return CustomerType.SENIOR
        return CustomerType.ADULT

    def clean(self):
        super().clean()
        a = self.age
        if self.date_of_birth:
            if self.date_of_birth > timezone.localdate():
                raise ValidationError({"date_of_birth": "Ngày sinh không được ở tương lai."})
            if a is not None and a > 120:
                raise ValidationError({"date_of_birth": "Ngày sinh không hợp lý (>120 tuổi)."})

        if a is None or self.customer_type is None:
            return
        ct = self.customer_type
        if a <= AGE_CHILD_MAX:
            if ct != CustomerType.CHILD:
                raise ValidationError({"customer_type": "Tuổi < 6: phải là 'Trẻ em'."})
            return
        if a <= AGE_STUDENT_MAX:
            if self.is_student:
                if ct != CustomerType.STUDENT:
                    raise ValidationError({"customer_type": "Đánh dấu HSSV & <23: phải chọn 'HSSV'."})
            else:
                if ct != CustomerType.ADULT:
                    raise ValidationError({"customer_type": "Dưới 23 nhưng không HSSV: chọn 'Người lớn'."})
            return
        if a <= AGE_SENIOR_MIN_EXCLUSIVE:
            if ct != CustomerType.ADULT:
                raise ValidationError({"customer_type": "Tuổi 23–60: phải là 'Người lớn'."})
            return
        if a > AGE_SENIOR_MIN_EXCLUSIVE:
            if ct != CustomerType.SENIOR:
                raise ValidationError({"customer_type": "Tuổi > 60: phải là 'Người già'."})

    def save(self, *args, **kwargs):
        if not self.username:
            self.username = self.email
        if self.customer_type is None and self.date_of_birth:
            sug = self.suggest_customer_type()
            if sug is not None:
                self.customer_type = sug
        super().save(*args, **kwargs)
