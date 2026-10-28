from datetime import date

from django.contrib import messages
from django.db.models import Count, Q
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone

from .models import Student, Attendance
from .forms import StudentForm




def dashboard(request):
    today = timezone.localdate()
    selected_date = today

    # Get the date selected by the user
    date_value = request.GET.get("date", "").strip()

    if date_value:
        try:
            selected_date = date.fromisoformat(date_value)

            # Do not allow future dates
            if selected_date > today:
                selected_date = today

        except ValueError:
            selected_date = today

    students = Student.objects.all()
    records = Attendance.objects.filter(date=selected_date)

    total = students.count()
    present = records.filter(status="Present").count()
    absent = records.filter(status="Absent").count()

    marked = present + absent
    unmarked = max(total - marked, 0)

    percentage = round(present * 100 / marked) if marked else 0

    context = {
        "total": total,
        "present": present,
        "absent": absent,
        "unmarked": unmarked,
        "percentage": percentage,
        "today": today,
        "selected_date": selected_date,
        "recent_students": students[:5],
    }

    return render(request, "attendance/dashboard.html", context)


def students_page(request):
    form = StudentForm()

    if request.method == "POST":
        form = StudentForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Student added successfully.")
            return redirect("students")

    search = request.GET.get("q", "").strip()
    students = Student.objects.all()

    if search:
        students = students.filter(
            Q(name__icontains=search)
            | Q(roll_number__icontains=search)
            | Q(branch__icontains=search)
        )

    return render(request, "attendance/students.html", {
        "form": form,
        "students": students,
        "search": search,
    })


def delete_student(request, student_id):
    if request.method == "POST":
        student = get_object_or_404(Student, id=student_id)
        student.delete()
        messages.success(request, "Student deleted successfully.")

    return redirect("students")


def attendance_page(request):
    today = timezone.localdate()
    selected_date = today

    if request.method == "POST":
        date_value = request.POST.get("date", "")

        try:
            selected_date = date.fromisoformat(date_value)
            if selected_date > today:
                messages.error(request, "Future dates are not allowed.")
                return redirect("attendance")
        except (ValueError, TypeError):
            messages.error(request, "Please select a valid date.")
            return redirect("attendance")

        students = Student.objects.all()

        for student in students:
            status = request.POST.get(f"status_{student.id}")

            if status in ("Present", "Absent"):
                Attendance.objects.update_or_create(
                    student=student,
                    date=selected_date,
                    defaults={"status": status},
                )
            else:
              Attendance.objects.filter(
              student=student,
              date=selected_date,
            ).delete()

        messages.success(
            request,
            f"Attendance saved for {selected_date.strftime('%d %b %Y')}."
        )
        return redirect(f"/attendance/?date={selected_date.isoformat()}")

    date_value = request.GET.get("date", "")

    if date_value:
        try:
            selected_date = date.fromisoformat(date_value)
            if selected_date > today:
                selected_date = today
        except ValueError:
            selected_date = today

    students = Student.objects.all()
    records = {
        record.student_id: record.status
        for record in Attendance.objects.filter(date=selected_date)
    }

    return render(request, "attendance/attendance.html", {
        "students": students,
        "selected_date": selected_date,
        "records": records,
        "today": today,
    })


def reports(request):
    students = Student.objects.annotate(
        total_days=Count("attendance_records"),
        present_days=Count(
            "attendance_records",
            filter=Q(attendance_records__status="Present")
        ),
        absent_days=Count(
            "attendance_records",
            filter=Q(attendance_records__status="Absent")
        ),
    )

    report_rows = []

    for student in students:
        total_days = student.total_days
        present_days = student.present_days
        percentage = (
            round(present_days * 100 / total_days, 1)
            if total_days else 0
        )

        report_rows.append({
            "student": student,
            "total_days": total_days,
            "present_days": present_days,
            "absent_days": student.absent_days,
            "percentage": percentage,
        })

    return render(request, "attendance/reports.html", {
        "report_rows": report_rows,
    })


def student_detail(request, student_id):
    student = get_object_or_404(Student, id=student_id)

    attendance_records = student.attendance_records.all().order_by("-date")

    total_days = attendance_records.count()
    present_days = attendance_records.filter(status="Present").count()
    absent_days = attendance_records.filter(status="Absent").count()

    percentage = (
        round(present_days * 100 / total_days, 1)
        if total_days else 0
    )

    context = {
        "student": student,
        "attendance_records": attendance_records,
        "total_days": total_days,
        "present_days": present_days,
        "absent_days": absent_days,
        "percentage": percentage,
    }

    return render(request, "attendance/student_detail.html", context)


def edit_student(request, student_id):
    student = get_object_or_404(Student, id=student_id)

    if request.method == "POST":
        form = StudentForm(request.POST, instance=student)

        if form.is_valid():
            form.save()
            messages.success(request, "Student updated successfully.")
            return redirect("students")
    else:
        form = StudentForm(instance=student)

    return render(request, "attendance/student_edit.html", {
        "form": form,
        "student": student,
    })


def attendance_filter(request):
    from datetime import date
    from django.utils import timezone
    from .models import Student, Attendance

    today = timezone.localdate()
    selected_date = today

    date_value = request.GET.get("date", "")
    if date_value:
        try:
            requested_date = date.fromisoformat(date_value)
            if requested_date <= today:
                selected_date = requested_date
        except ValueError:
            pass

    status = request.GET.get("status", "")

    if status == "Present":
        student_ids = Attendance.objects.filter(
            date=selected_date,
            status="Present"
        ).values_list("student_id", flat=True)

        students = Student.objects.filter(id__in=student_ids)

        page_title = "Present Students"

    elif status == "Absent":
        student_ids = Attendance.objects.filter(
            date=selected_date,
            status="Absent"
        ).values_list("student_id", flat=True)

        students = Student.objects.filter(id__in=student_ids)

        page_title = "Absent Students"

    elif status == "Not Marked":
        marked_ids = Attendance.objects.filter(
            date=selected_date
        ).values_list("student_id", flat=True)

        students = Student.objects.exclude(id__in=marked_ids)

        page_title = "Attendance Not Marked"

    else:
        students = Student.objects.none()
        page_title = "Attendance Details"

    return render(request, "attendance/attendance_filter.html", {
        "students": students,
        "selected_date": selected_date,
        "page_title": page_title,
        "status": status,
    })

# ===== ATTENDEASE LOGIN SYSTEM =====

from datetime import date as date_type
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from .models import Student, Attendance


def user_login(request):
    if request.user.is_authenticated:
        if request.user.is_staff or request.user.is_superuser:
            return redirect("dashboard")
        return redirect("student_profile")

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is not None:
            # Institute/Admin account
            if user.is_staff or user.is_superuser:
                login(request, user)
                return redirect("dashboard")

            # Student account: verify existing student record
            if Student.objects.filter(roll_number=user.username).exists():
                login(request, user)
                return redirect("student_profile")

        messages.error(request, "Username ya password galat hai.")

    return render(request, "attendance/login.html")


def student_register(request):
    if request.user.is_authenticated:
        return redirect("dashboard" if (
            request.user.is_staff or request.user.is_superuser
        ) else "student_profile")

    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        roll_number = request.POST.get("roll_number", "").strip()
        password = request.POST.get("password", "")
        confirm_password = request.POST.get("confirm_password", "")

        student = Student.objects.filter(
            name__iexact=name,
            roll_number__iexact=roll_number
        ).first()

        if not student:
            messages.error(
                request,
                "Student record nahi mila. Name aur roll number check karo."
            )
        elif User.objects.filter(username__iexact=student.roll_number).exists():
            messages.error(
                request,
                "Is roll number ka account pehle se bana hua hai. Login karo."
            )
        elif len(password) < 8:
            messages.error(
                request,
                "Password kam se kam 8 characters ka hona chahiye."
            )
        elif password != confirm_password:
            messages.error(request, "Dono passwords match nahi karte.")
        else:
            user = User.objects.create_user(
                username=student.roll_number,
                password=password
            )
            user.first_name = student.name
            user.save()

            login(request, user)
            messages.success(request, "Registration successful!")
            return redirect("student_profile")

    return render(request, "attendance/register.html")


@login_required(login_url="login")
def student_profile(request):
    if request.user.is_staff or request.user.is_superuser:
        return redirect("dashboard")

    student = Student.objects.filter(
        roll_number__iexact=request.user.username
    ).first()

    if not student:
        logout(request)
        messages.error(request, "Student record nahi mila. Institute se contact karo.")
        return redirect("login")

    records = Attendance.objects.filter(student=student).order_by("-date")

    total_classes = records.count()
    present_count = records.filter(status="Present").count()
    absent_count = records.filter(status="Absent").count()

    percentage = round(
        (present_count / total_classes) * 100, 2
    ) if total_classes else 0

    return render(request, "attendance/student_profile.html", {
        "student": student,
        "records": records,
        "total_classes": total_classes,
        "present_count": present_count,
        "absent_count": absent_count,
        "percentage": percentage,
    })


# def user_logout(request):
#     logout(request)
#     return redirect("login")

