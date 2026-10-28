from django.contrib import admin
from .models import Student, Attendance


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ("roll_number", "name", "branch", "created_at")
    search_fields = ("roll_number", "name", "branch")
    ordering = ("roll_number",)


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ("student", "date", "status")
    list_filter = ("date", "status")
    search_fields = ("student__name", "student__roll_number")