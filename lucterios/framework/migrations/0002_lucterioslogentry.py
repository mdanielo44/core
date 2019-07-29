# Generated by Django 2.2.3 on 2019-07-29 09:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('framework', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='LucteriosLogEntry',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('modelname', models.CharField(db_index=True, max_length=255, verbose_name='content type')),
                ('username', models.CharField(blank=True, default=None, max_length=255, null=True, verbose_name='actor')),
                ('object_pk', models.CharField(db_index=True, max_length=255, verbose_name='object pk')),
                ('object_id', models.BigIntegerField(blank=True, db_index=True, null=True, verbose_name='object id')),
                ('object_repr', models.TextField(verbose_name='object representation')),
                ('action', models.IntegerField(choices=[(0, 'create'), (1, 'update'), (2, 'delete')], verbose_name='action')),
                ('changes', models.TextField(blank=True, verbose_name='change message')),
                ('remote_addr', models.GenericIPAddressField(blank=True, null=True, verbose_name='remote address')),
                ('timestamp', models.DateTimeField(auto_now_add=True, verbose_name='timestamp')),
                ('additional_data', models.TextField(blank=True, null=True, verbose_name='additional data')),
            ],
            options={
                'verbose_name': 'log entry',
                'verbose_name_plural': 'log entries',
                'ordering': ['-timestamp'],
                'get_latest_by': 'timestamp',
                'default_permissions': [],
            },
        ),
    ]