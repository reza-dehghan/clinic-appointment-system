from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("appointments", "0002_initial"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="appointment",
            name="time_slot",
        ),
        migrations.AddField(
            model_name="appointment",
            name="start_time",
            field=models.DateTimeField(default="2026-01-01T00:00:00Z"),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="appointment",
            name="end_time",
            field=models.DateTimeField(default="2026-01-01T00:30:00Z"),
            preserve_default=False,
        ),
        migrations.AddConstraint(
            model_name="appointment",
            constraint=models.UniqueConstraint(
                fields=("doctor", "start_time"),
                name="unique_doctor_appointment_start",
            ),
        ),
        migrations.AddConstraint(
            model_name="appointment",
            constraint=models.CheckConstraint(
                condition=models.Q(("start_time__lt", models.F("end_time"))),
                name="appointment_start_before_end",
            ),
        ),
        migrations.AddIndex(
            model_name="appointment",
            index=models.Index(
                fields=["doctor", "start_time"], name="appointment_doctor_start_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="appointment",
            index=models.Index(
                fields=["clinic", "start_time"], name="appointment_clinic_start_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="appointment",
            index=models.Index(
                fields=["status", "start_time"], name="appointment_status_start_idx"
            ),
        ),
    ]
