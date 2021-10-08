# Generated by Django 2.2.16 on 2021-09-27 09:36

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("posts", "0003_post_group"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="post",
            options={"ordering": ["-pub_date"]},
        ),
        migrations.AlterField(
            model_name="group",
            name="title",
            field=models.CharField(max_length=200, verbose_name="Название группы"),
        ),
        migrations.AlterField(
            model_name="post",
            name="group",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="posts",
                to="posts.Group",
            ),
        ),
    ]