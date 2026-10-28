from django.contrib import admin
from . import models
for name in dir(models):
 obj=getattr(models,name)
 if isinstance(obj,type) and getattr(obj,'_meta',None) is not None and not obj._meta.abstract and obj._meta.app_label=='audit':
  try: admin.site.register(obj)
  except admin.sites.AlreadyRegistered: pass
