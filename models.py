
from django.db import models
from django.conf import settings



class Student(models.Model):
    BRANCH_CHOICES = [
        ("CSE", "CSE"),
        ("EE", "EE"),
        ("ECE", "ECE"),
        ("BIOTEC", "BIOTEC"),
        ("ME", "ME"),
    ]

    roll_number = models.CharField(max_length=30, unique=True)
    name = models.CharField(max_length=100)
    branch = models.CharField(
        max_length=100,
        choices=BRANCH_CHOICES,
        default="CSE"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.OneToOneField(
    settings.AUTH_USER_MODEL,
    on_delete=models.SET_NULL,
    null=True,
    blank=True,
    related_name="student_profile"
)

    class Meta:
        ordering = ["roll_number"]

    def __str__(self):
        return f"{self.roll_number} - {self.name}"


class Attendance(models.Model):
    STATUS_CHOICES = [
        ("Present", "Present"),
        ("Absent", "Absent"),
    ]

    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name="attendance_records"
    )
    date = models.DateField()
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default="Present"
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["student", "date"],
                name="unique_student_attendance_per_day"
            )
        ]
        ordering = ["student__roll_number"]

    def __str__(self):
        return f"{self.student.name} - {self.date} - {self.status}"
