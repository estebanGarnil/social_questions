from django.contrib import admin

from .models import (
    Collaboration,
    Exploration,
    Question,
    QuestionList,
    QuestionView,
    Subscription,
)


@admin.register(QuestionList)
class QuestionListAdmin(admin.ModelAdmin):
    list_display = ("name", "owner", "visibility", "is_active", "created_at")
    list_filter = ("visibility", "is_active")
    search_fields = ("name", "description", "owner__email")


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ("short_text", "question_list", "author", "is_active")
    list_filter = ("is_active",)
    search_fields = ("text", "question_list__name", "author__email")

    @admin.display(description="Question")
    def short_text(self, obj: Question) -> str:
        return obj.text[:80]


admin.site.register(Collaboration)
admin.site.register(Subscription)
admin.site.register(Exploration)
admin.site.register(QuestionView)
