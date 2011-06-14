# -*- coding: utf-8 -*-


from django.db import models


class MockConfig(models.Model):
    name        = models.CharField(max_length=256, unique=True)
    enabled     = models.BooleanField(default=True)

    class Meta:
        ordering = ("name", )

    def __unicode__(self):
        return self.name

    def export(self):
        result = {
            "name": self.name,
            "enabled": self.enabled,
        }
        return result
