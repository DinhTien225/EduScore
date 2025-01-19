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
    index_title = "Welcome to EduScore Admin "

    def get_urls(self):
        return [path('score-stats/', self.stats)] + super().get_urls()

    def stats(self,request):
        stats_by_department = (
            DisciplinePoint.objects.values('student__groups__name')
            .annotate(
                total_score=Sum('score'),
                avg_score=Avg('score'),
                student_count=Count('student', distinct=True)
            )
        )

        # Thống kê xếp loại
        classification = (
            DisciplinePoint.objects.values('student__groups__name')
            .annotate(
                excellent=Count('total_score', filter=Q(total_score__gte=90)),
                good=Count('total_score', filter=Q(total_score__gte=75, total_score__lt=90)),
                average=Count('total_score', filter=Q(total_score__gte=50, total_score__lt=75)),
                poor=Count('total_score', filter=Q(total_score__lt=50)),
            )
        )

        context = {
            'stats_by_department': stats_by_department,
            'classification': classification,
        }
        return TemplateResponse(request, 'admin/stats.html', context)

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

class DisciplinePointAdmin(BaseAdmin):
    list_display = ('student', 'criteria', 'score', 'total_score')
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
admin_site.register(DisciplinePoint, DisciplinePointAdmin)
admin_site.register(Report, ReportAdmin)
admin_site.register(NewsFeed, NewsFeedAdmin)
admin_site.register(Like, LikeAdmin)
admin_site.register(Comment, CommentAdmin)
admin_site.register(Message, MessageAdmin)
admin_site.register(Tag)