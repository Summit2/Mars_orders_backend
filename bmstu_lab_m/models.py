
from django.db import models
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import AbstractUser, Group, Permission

class AuthGroup(models.Model):
    name = models.CharField(unique=True, max_length=150)

    class Meta:
        managed = False
        db_table = 'auth_group'


class AuthGroupPermissions(models.Model):
    id = models.BigAutoField(primary_key=True)
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)
    permission = models.ForeignKey('AuthPermission', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_group_permissions'
        unique_together = (('group', 'permission'),)


class AuthPermission(models.Model):
    name = models.CharField(max_length=255)
    content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING)
    codename = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'auth_permission'
        unique_together = (('content_type', 'codename'),)


class AuthUser(models.Model):
    password = models.CharField(max_length=128)
    last_login = models.DateTimeField(blank=True, null=True)
    is_superuser = models.BooleanField()
    username = models.CharField(unique=True, max_length=150)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    email = models.CharField(max_length=254)
    is_staff = models.BooleanField()
    is_active = models.BooleanField()
    date_joined = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'auth_user'


class AuthUserGroups(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_user_groups'
        unique_together = (('user', 'group'),)


class AuthUserUserPermissions(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)
    permission = models.ForeignKey(AuthPermission, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_user_user_permissions'
        unique_together = (('user', 'permission'),)


class Cargo(models.Model):
    id_cargo = models.AutoField(primary_key=True)
    title = models.CharField(max_length=50, blank=True, null=True)
    image_url = models.CharField(max_length=100, blank=True, null=True)
    weight = models.IntegerField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    is_deleted = models.BooleanField(blank=True, null=True)
    image_binary = models.BinaryField(blank=True, null=True)
    class Meta:
        managed = False
        db_table = 'cargo'

    def save_binary_data_from_file_path(self, file_path):
        with open(file_path, 'rb') as file:
            binary_data = file.read()
            self.image_binary = binary_data
        self.save()

    
class CargoOrder(models.Model):
    id_cargo = models.ForeignKey(Cargo, models.DO_NOTHING, db_column='id_cargo')
    id_order = models.OneToOneField('DeliveryOrders', models.DO_NOTHING, db_column='id_order', primary_key=True)  # The composite primary key (id_order, id_cargo) found, that is not supported. The first column is selected.
    amount = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'cargo_order'
        unique_together = (('id_order', 'id_cargo'),)     
#     id_cargo = models.ForeignKey(Cargo, models.DO_NOTHING, db_column='id_cargo', blank=True, null=True)
#     id_order = models.ForeignKey('DeliveryOrders', models.DO_NOTHING, db_column='id_order', blank=True, null=True)

#     class Meta:
#         managed = False
#         db_table = 'cargo_order'


class DeliveryOrders(models.Model):
    id_order = models.AutoField(primary_key=True)
    id_user = models.ForeignKey('Users', models.DO_NOTHING, db_column='id_user', blank=True, null=True)
    id_moderator = models.ForeignKey('Users', models.DO_NOTHING, db_column='id_moderator', related_name='deliveryorders_id_moderator_set', blank=True, null=True)
    order_status = models.CharField(max_length=200, blank=True, null=True) #order_status::text ~~ 'введён'::text OR order_status::text ~~ 'в работе'::text OR order_status::text ~~ 'завершён'::text OR order_status::text ~~ 'отменён'::text OR order_status::text ~~ 'удалён'::text
    date_create = models.DateField(blank=True, null=True)
    date_accept = models.DateField(blank=True, null=True)
    date_finish = models.DateField(blank=True, null=True)
    is_delivered = models.BooleanField(null=True)

    class Meta:
        managed = False
        db_table = 'delivery_orders'


class DjangoAdminLog(models.Model):
    action_time = models.DateTimeField()
    object_id = models.TextField(blank=True, null=True)
    object_repr = models.CharField(max_length=200)
    action_flag = models.SmallIntegerField()
    change_message = models.TextField()
    content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING, blank=True, null=True)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'django_admin_log'


class DjangoContentType(models.Model):
    app_label = models.CharField(max_length=100)
    model = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'django_content_type'
        unique_together = (('app_label', 'model'),)


class DjangoMigrations(models.Model):
    id = models.BigAutoField(primary_key=True)
    app = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    applied = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_migrations'


class DjangoSession(models.Model):
    session_key = models.CharField(primary_key=True, max_length=200)
    session_data = models.TextField()
    expire_date = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_session'


class Users(models.Model):
    first_name = models.CharField(max_length=200, blank=True, null=True)
    last_name = models.CharField(max_length=200, blank=True, null=True)
    email = models.CharField(unique=True, max_length=254, blank=True, null=True)
    passwd = models.CharField(max_length=500, blank=True, null=True)
    id_user = models.AutoField(primary_key=True)
    is_moderator = models.BooleanField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'users'
    