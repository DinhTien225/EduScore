from django.contrib import admin
from django.db.models import Count, Sum, Avg,Q
from django.template.response import TemplateResponse
from django.utils.safestring import mark_safe
from scores.models import *
from django import forms
from ckeditor_uploader.widgets import CKEditorUploadingWidget
from django.urls import path

class MyScoreAdmin(admin.AdminSite):
    site_header = 'Edu Scores'
    site_title = "EduScore Admin"
    index_title = "Welcome to EduScore Admin"

    def get_urls(self):
        return [
            path('score-stats/', self.stats),
            path('export-csv/', self.export_csv),
            path('export-pdf/', self.export_pdf),
        ] + super().get_urls()

    def stats(self, request):
        # Lấy danh sách các lớp
        all_classes = Class.objects.all()

        # Lấy lớp được chọn từ request
        selected_class_id = request.GET.get('class')
        if selected_class_id:
            # Lọc thống kê theo lớp được chọn
            stats_by_class = (
                DisciplinePoint.objects.filter(student__student_class__id=selected_class_id)
                .values('student__student_class__name')
                .annotate(
                    total_score=Sum('score'),
                    avg_score=Avg('score'),
                    student_count=Count('student', distinct=True)
                )
            )
            classification = (
                DisciplinePoint.objects.filter(student__student_class__id=selected_class_id)
                .values('student__student_class__name')
                .annotate(
                    excellent=Count('score', filter=Q(score__gte=90)),
                    good=Count('score', filter=Q(score__gte=75, score__lt=90)),
                    average=Count('score', filter=Q(score__gte=50, score__lt=75)),
                    poor=Count('score', filter=Q(score__lt=50)),
                )
            )
        else:
            # Hiển thị thống kê cho tất cả các lớp
            stats_by_class = (
                DisciplinePoint.objects.values('student__student_class__name')
                .annotate(
                    total_score=Sum('score'),
                    avg_score=Avg('score'),
                    student_count=Count('student', distinct=True)
                )
            )
            classification = (
                DisciplinePoint.objects.values('student__student_class__name')
                .annotate(
                    excellent=Count('score', filter=Q(score__gte=90)),
                    good=Count('score', filter=Q(score__gte=75, score__lt=90)),
                    average=Count('score', filter=Q(score__gte=50, score__lt=75)),
                    poor=Count('score', filter=Q(score__lt=50)),
                )
            )

        context = {
            'all_classes': all_classes,
            'selected_class_id': int(selected_class_id) if selected_class_id else None,
            'stats_by_class': stats_by_class,
            'classification': classification,
        }

        return TemplateResponse(request, 'admin/stats.html', context)

    def export_csv(self, request):
        # Xuất danh sách chi tiết dưới dạng CSV
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="discipline_points.csv"'

        writer = csv.writer(response)
        writer.writerow(['Student', 'Class', 'Department', 'Score', 'Description', 'Created At'])

        points = DisciplinePoint.objects.select_related('student', 'student__department', 'student__student_class')
        for point in points:
            writer.writerow([
                point.student.username,
                point.student.student_class.name if point.student.student_class else '',
                point.student.department.name if point.student.department else '',
                point.score,
                point.description,
                point.created_at,
            ])

        return response

    def export_pdf(self, request):
        # Xuất danh sách chi tiết dưới dạng PDF
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="discipline_points.pdf"'

        buffer = BytesIO()
        p = canvas.Canvas(buffer, pagesize=A4)

        # Tiêu đề
        p.setFont("Helvetica-Bold", 16)
        p.drawString(200, 800, "Discipline Points Report")
        p.setFont("Helvetica", 12)

        # Nội dung
        y = 750
        points = DisciplinePoint.objects.select_related('student', 'student__department', 'student__student_class')
        for point in points:
            if y < 50:  # Tạo trang mới nếu hết chỗ
                p.showPage()
                y = 750
            p.drawString(50, y, f"Student: {point.student.username}, Class: {point.student.student_class.name if point.student.student_class else ''}, "
                                 f"Score: {point.score}, Description: {point.description}")
            y -= 20

        p.save()
        buffer.seek(0)
        response.write(buffer.getvalue())
        buffer.close()
        return response

class BaseAdmin(admin.ModelAdmin):
    class Media:
        css = {
            'all': ('/static/css/styles.css',)
        }

class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'is_superuser')
    search_fields = ('username', 'email')
    list_filter = ('is_staff', 'is_superuser')
    ordering = ('username',)

    def save_model(self, request, obj, form, change):
        if 'password' in form.changed_data:
            obj.set_password(obj.password)
        super().save_model(request, obj, form, change)


class ActivityForm(forms.ModelForm):
    description = forms.CharField(widget=CKEditorUploadingWidget)

    class Meta:
        model = Activity
        fields = '__all__'

class ActivityAdmin(BaseAdmin):
    list_display = ('title', 'start_date', 'end_date', 'status', 'created_by')
    list_filter = ('status', 'category')
    search_fields = ('title', 'description')
    ordering = ('start_date',)
    form=ActivityForm
    readonly_fields = ['IMAGE']

    def IMAGE(self, activity):
        if activity.image:
            return mark_safe(f"<img src='/static/{activity.image.name}' width='120'/>")
        return "No image"

class CategoryAdmin(BaseAdmin):
    pass

class ParticipationAdmin(BaseAdmin):
    list_display = ('student', 'activity', 'is_completed')
    list_filter = ('is_completed', 'activity')
    readonly_fields = ['image']

    def image(self, participation):
        if participation.proof:
            return mark_safe(f"<img src='/static/{participation.proof.name}' width='120'/>")
        return "No image"

class EvaluationCriteriaAdmin(admin.ModelAdmin):
    list_display = ('name', 'group', 'score', 'active', 'created_date')
    list_filter = ('group', 'active', 'created_date')
    search_fields = ('name', 'group__name')
    ordering = ('group', 'name')
    list_editable = ('score', 'active')

class EvaluationGroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'max_score', 'active', 'created_date')
    search_fields = ('name',)
    list_editable = ('max_score', 'active')

class DisciplinePointAdmin(BaseAdmin):
    list_display = ('student', 'criteria', 'score', 'group_total_score')
    list_filter = ('student',)

class ReportAdmin(BaseAdmin):
    list_display = ('student', 'activity', 'status', 'handled_by')
    list_filter = ('status', 'activity', 'student')
    search_fields = ('student__username', 'activity__title')
    readonly_fields = ['image']

    def image(self, report):
        if report.proof:
            return mark_safe(f"<img src='/static/{report.proof.name}' width='120'/>")
        return "No image"

class NewsFeedAdmin(BaseAdmin):
    list_display = ('activity', 'created_by', 'timestamp')
    search_fields = ('activity__title',)
    list_filter = ('created_date',)

class LikeAdmin(BaseAdmin):
    list_display = ('user', 'newsfeed')

class CommentAdmin(BaseAdmin):
    list_display = ('user', 'newsfeed', 'content')
    search_fields = ('content',)

class MessageAdmin(BaseAdmin):
    list_display = ('sender', 'receiver', 'content', 'timestamp')
    search_fields = ('sender__username', 'receiver__username', 'content')
    list_filter = ('sender', 'receiver')

admin_site=MyScoreAdmin(name='EduScore')

admin_site.register(User, UserAdmin)
admin_site.register(Department)
admin_site.register(Class)
admin_site.register(Category,CategoryAdmin)
admin_site.register(Activity, ActivityAdmin)
admin_site.register(Participation, ParticipationAdmin)
admin_site.register(EvaluationCriteria, EvaluationCriteriaAdmin)
admin_site.register(EvaluationGroup, EvaluationGroupAdmin)
admin_site.register(DisciplinePoint, DisciplinePointAdmin)
admin_site.register(Report, ReportAdmin)
admin_site.register(NewsFeed, NewsFeedAdmin)
admin_site.register(Like, LikeAdmin)
admin_site.register(Comment, CommentAdmin)
admin_site.register(Message, MessageAdmin)
admin_site.register(Tag)