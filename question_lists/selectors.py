from django.db.models import Q, QuerySet

from .models import QuestionList


def accessible_question_lists(user) -> QuerySet[QuestionList]:
    """Return active lists visible to the supplied user."""
    queryset = QuestionList.objects.filter(is_active=True)
    if not user or not user.is_authenticated:
        return queryset.filter(visibility=QuestionList.Visibility.PUBLIC)

    return queryset.filter(
        Q(visibility=QuestionList.Visibility.PUBLIC) | Q(owner=user) | Q(collaborations__user=user)
    ).distinct()
