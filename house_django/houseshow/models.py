# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey has `on_delete` set to the desired behavior.
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models


class Zufang(models.Model):
    zone = models.CharField(max_length=20)
    housetype = models.CharField(max_length=20)
    houseurl = models.CharField(max_length=1000)
    imgurl = models.CharField(max_length=1000)
    housenum = models.PositiveIntegerField()
    price = models.PositiveSmallIntegerField()
    housearea = models.PositiveSmallIntegerField()
    per_price = models.PositiveIntegerField()
    city = models.CharField(max_length=10)

    class Meta:
        managed = False
        db_table = 'zufang'

