from django.db import models


class Cargo(models.Model):
    id_cargo = models.AutoField(primary_key=True)
    title = models.CharField(max_length=50, blank=True, null=True)
    image_url = models.CharField(max_length=100, blank=True, null=True)
    weight = models.IntegerField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    is_deleted = models.BooleanField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'cargo'


class CargoOrder(models.Model):
    id_cargo = models.ForeignKey(Cargo, models.DO_NOTHING, db_column='id_cargo', blank=True, null=True)
    id_order = models.ForeignKey('DeliveryOrders', models.DO_NOTHING, db_column='id_order', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'cargo_order'


class DeliveryOrders(models.Model):
    id_order = models.AutoField(primary_key=True)
    id_user = models.ForeignKey('Users', models.DO_NOTHING, db_column='id_user', blank=True, null=True)
    id_moderator = models.ForeignKey('Users', models.DO_NOTHING, db_column='id_moderator', related_name='deliveryorders_id_moderator_set', blank=True, null=True)
    order_status = models.CharField(max_length=40, blank=True, null=True)
    date_create = models.DateField(blank=True, null=True)
    date_accept = models.DateField(blank=True, null=True)
    date_finish = models.DateField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'delivery_orders'


class Users(models.Model):
    first_name = models.CharField(max_length=30, blank=True, null=True)
    last_name = models.CharField(max_length=40, blank=True, null=True)
    email = models.CharField(unique=True, max_length=50, blank=True, null=True)
    passwd = models.CharField(max_length=40, blank=True, null=True)
    id_user = models.AutoField(primary_key=True)
    is_moderator = models.BooleanField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'users'