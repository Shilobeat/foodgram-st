from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_auto_20251223_1321'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='user',
            name='is_subscribed',
        ),
    ]
