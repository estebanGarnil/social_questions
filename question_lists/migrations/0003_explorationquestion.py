from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):
    dependencies = [
        ("question_lists", "0002_exploration_sessions"),
    ]

    operations = [
        migrations.CreateModel(
            name="ExplorationQuestion",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("position", models.PositiveSmallIntegerField()),
                (
                    "exploration",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="selected_questions",
                        to="question_lists.exploration",
                    ),
                ),
                (
                    "question",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="session_selections",
                        to="question_lists.question",
                    ),
                ),
            ],
            options={
                "ordering": ("position",),
            },
        ),
        migrations.AddConstraint(
            model_name="explorationquestion",
            constraint=models.UniqueConstraint(
                fields=("exploration", "question"),
                name="unique_question_per_session_selection",
            ),
        ),
        migrations.AddConstraint(
            model_name="explorationquestion",
            constraint=models.UniqueConstraint(
                fields=("exploration", "position"),
                name="unique_position_per_session_selection",
            ),
        ),
    ]
