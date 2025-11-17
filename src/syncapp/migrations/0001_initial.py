from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='SyncResult',
            fields=[
                ('id', models.BigAutoField(
                    auto_created=True,
                    primary_key=True,
                    serialize=False,
                    verbose_name='ID')
                 ),
                ('started_at', models.DateTimeField(auto_now_add=True)),
                ('finished_at', models.DateTimeField(blank=True, null=True)),
                ('full_sync', models.BooleanField(default=False)),
                ('changed_from', models.DateTimeField(blank=True, null=True)),
                ('changed_to', models.DateTimeField(blank=True, null=True)),
                ('added', models.IntegerField(default=0)),
                ('updated', models.IntegerField(default=0)),
                ('raw_response_summary', models.TextField(blank=True)),
            ],
            options={
                'ordering': ('-started_at',),
            },
        ),
    ]
