import uuid

from django.db import migrations, models


def mark_existing_completed_lists(apps, schema_editor):
    exploration = apps.get_model("question_lists", "Exploration")
    exploration.objects.filter(status="completed").update(list_completed=True)


class Migration(migrations.Migration):
    dependencies = [
        ("question_lists", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="exploration",
            name="cycle_id",
            field=models.UUIDField(db_index=True, default=uuid.uuid4, editable=False),
        ),
        migrations.AddField(
            model_name="exploration",
            name="list_completed",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="exploration",
            name="question_limit",
            field=models.PositiveSmallIntegerField(default=20),
        ),
        migrations.RunPython(
            mark_existing_completed_lists,
            migrations.RunPython.noop,
        ),
    ]
