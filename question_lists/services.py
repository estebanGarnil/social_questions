import uuid
from dataclasses import dataclass

from django.db import transaction

from .models import Exploration, Question, QuestionList, QuestionView

MAX_QUESTIONS_PER_SESSION = 20


class EmptyQuestionListError(Exception):
    """Raised when a list contains no active question."""


@dataclass(frozen=True)
class PickResult:
    question: Question
    exploration: Exploration
    session_viewed_count: int
    session_target_count: int
    session_completed: bool
    list_viewed_count: int
    total_count: int
    list_completed: bool


def _cycle_viewed_count(*, user, question_list: QuestionList, cycle_id) -> int:
    return (
        QuestionView.objects.filter(
            exploration__user=user,
            exploration__question_list=question_list,
            exploration__cycle_id=cycle_id,
            question__is_active=True,
        )
        .values("question_id")
        .distinct()
        .count()
    )


def _create_exploration(*, user, question_list: QuestionList, total_count: int) -> Exploration:
    latest = (
        Exploration.objects.filter(
            user=user,
            question_list=question_list,
        )
        .order_by("-created_at")
        .first()
    )
    cycle_id = latest.cycle_id if latest and not latest.list_completed else uuid.uuid4()
    return Exploration.objects.create(
        user=user,
        question_list=question_list,
        cycle_id=cycle_id,
        question_limit=min(MAX_QUESTIONS_PER_SESSION, total_count),
    )


@transaction.atomic
def pick_random_question(
    *,
    user,
    question_list: QuestionList,
    restart_session: bool = False,
) -> PickResult:
    """
    Pick an unseen question from the current user's active exploration.

    The exploration row is locked so two simultaneous requests for the same
    user and list cannot normally return the same question.
    """
    total_count = question_list.questions.filter(is_active=True).count()
    if total_count == 0:
        raise EmptyQuestionListError

    exploration = (
        Exploration.objects.select_for_update()
        .filter(
            user=user,
            question_list=question_list,
            status=Exploration.Status.IN_PROGRESS,
        )
        .first()
    )

    if restart_session and exploration is not None:
        session_viewed_count = exploration.question_views.count()
        list_viewed_count = _cycle_viewed_count(
            user=user,
            question_list=question_list,
            cycle_id=exploration.cycle_id,
        )
        exploration.complete(
            session_viewed_count,
            list_completed=list_viewed_count >= total_count,
        )
        exploration = None

    if exploration is None:
        exploration = _create_exploration(
            user=user,
            question_list=question_list,
            total_count=total_count,
        )

    session_viewed_question_ids = exploration.question_views.values("question_id")
    session_candidates = question_list.questions.filter(is_active=True).exclude(
        id__in=session_viewed_question_ids
    )
    cycle_viewed_question_ids = QuestionView.objects.filter(
        exploration__user=user,
        exploration__question_list=question_list,
        exploration__cycle_id=exploration.cycle_id,
    ).values("question_id")
    question = session_candidates.exclude(id__in=cycle_viewed_question_ids).order_by("?").first()

    # Une série privilégie les questions inédites, puis se complète avec des
    # questions déjà vues sans doublon à l'intérieur de la série actuelle.
    if question is None:
        question = session_candidates.order_by("?").first()

    # Défense contre une liste modifiée pendant une série.
    if question is None:
        list_viewed_count = _cycle_viewed_count(
            user=user,
            question_list=question_list,
            cycle_id=exploration.cycle_id,
        )
        exploration.complete(
            exploration.question_views.count(),
            list_completed=list_viewed_count >= total_count,
        )
        exploration = _create_exploration(
            user=user,
            question_list=question_list,
            total_count=total_count,
        )
        question = question_list.questions.filter(is_active=True).order_by("?").first()

    QuestionView.objects.create(
        exploration=exploration,
        question=question,
    )

    session_viewed_count = exploration.question_views.count()
    list_viewed_count = _cycle_viewed_count(
        user=user,
        question_list=question_list,
        cycle_id=exploration.cycle_id,
    )
    list_completed = list_viewed_count >= total_count
    session_completed = session_viewed_count >= exploration.question_limit
    if session_completed:
        exploration.complete(
            session_viewed_count,
            list_completed=list_completed,
        )

    return PickResult(
        question=question,
        exploration=exploration,
        session_viewed_count=session_viewed_count,
        session_target_count=exploration.question_limit,
        session_completed=session_completed,
        list_viewed_count=list_viewed_count,
        total_count=total_count,
        list_completed=list_completed,
    )


def user_list_progress(*, user, question_list: QuestionList) -> dict:
    """Return progress scoped to one user and one list."""
    total_count = question_list.questions.filter(is_active=True).count()
    latest = (
        Exploration.objects.filter(user=user, question_list=question_list)
        .order_by("-created_at")
        .first()
    )
    has_active_cycle = latest is not None and not latest.list_completed
    viewed_count = (
        _cycle_viewed_count(
            user=user,
            question_list=question_list,
            cycle_id=latest.cycle_id,
        )
        if has_active_cycle
        else 0
    )
    completed_count = Exploration.objects.filter(
        user=user,
        question_list=question_list,
        list_completed=True,
    ).count()

    percentage = round((viewed_count / total_count) * 100, 2) if total_count else 0
    return {
        "exploration_id": (
            latest.id if latest and latest.status == Exploration.Status.IN_PROGRESS else None
        ),
        "viewed_count": viewed_count,
        "total_count": total_count,
        "percentage": percentage,
        "completed_count": completed_count,
    }
