from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("myapp", "0004_auto_20191031_1429")]
    operations = [
        migrations.CreateModel(
            name="SiteViews",
            fields=[
                ("name", models.CharField(max_length=64, primary_key=True, serialize=False)),
                ("total", models.BigIntegerField()),
                ("imported_total", models.BigIntegerField()),
                ("imported_at", models.DateTimeField()),
            ],
            options={
                "verbose_name": "網站累積瀏覽數",
                "verbose_name_plural": "網站累積瀏覽數",
            },
        ),
    ]
