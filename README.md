# dj-la-library-system
Django Library Management System

- `pip install -e git+git://github.com/laborautonomo/dj-la-library-system.git@v0.1.0#egg=dj-la-library-system`
- execute `./manage.py makemigrations && ./manage.py migrate` (this line prevent the error [InvalidBasesError: Cannot resolve bases for...](http://stackoverflow.com/questions/30267237/invalidbaseserror-cannot-resolve-bases-for-modelstate-users-groupproxy))
- Add `library_sys.apps.LibrarySysConfig` into `INSTALLED_APPS` of `settings.py` 
- execute `./manage.py makemigrations && ./manage.py migrate` 
- Include library_sys URLconf. Ex.: 
    - Import the include() function: `from django.conf.urls import url, include` 
    - Add a URL to urlpatterns:  `url(r'^', include('library_sys.urls')),`

### Implement a default layout (optional): 
- Create `base.html` into your root template with content:
``` html
{% extends "layout_libsys_0.1.0/base.html" %}
{% block title %}Actual Page{% endblock %}
{% block title2 %}Project name{% endblock %}
{% block site_title %}This is my library management system{% endblock %}
```
- Change layout images:
    - Create directories `library_sys/static/library_sys/img/`
    - Put images `bg.jpg`, `logo.png`, `favicon.png` and `search.png`
    - Add `os.path.join(BASE_DIR, 'library_sys/static'),` into `STATICFILES_DIRS` on `settings.py`