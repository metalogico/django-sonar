# DjangoSonar

The missing debug tool for django.

DjangoSonar is a comprehensive debugging and introspection tool for Django applications, inspired by Laravel Telescope.


![cover-image](https://github.com/metalogico/django-sonar/assets/7287030/32183dcb-5cf5-4878-b27c-3a34a6aa4ba1)



## 🥳 Motivation

Having spent years developing with Laravel before switching to Django, the first thing I missed from this change was the amazing [Laravel Telescope](https://github.com/laravel/telescope). So, I decided to create it myself.

DjangoSonar is built using:
- [Django](https://www.djangoproject.com/)
- [Bootstrap 5](https://getbootstrap.com/)
- [htmx](https://htmx.org/)

If you use this project, please consider giving it a ⭐.

## ⭐ Features

- Self updating lists of:
  - Requests
  - Exceptions
  - Queries
  - Dumps 
  - (Signals coming soon™)
- Request insights:
  - Payload get/post
  - Auth User
  - Session vars
  - Headers
  - ...
- Historical data (clearable)
- Simple and reactive UI


## 🛠️ How to install 

1. First you need to install the package:

```bash
pip install django-sonar
```

2. Then, to enable the dashboard, you will need to add the app to the **INSTALLED_APPS** in your project main settings file:

```python
INSTALLED_APPS = [
    ...
    'django_sonar',
    ...
]
```

3. Add the urls to the main **urls.py file** in your project folder:

```python
urlpatterns = [
    ...
    path('sonar/', include('django_sonar.urls')),
    ...
]
```

4. 🔔 Be sure to add the **exclusions settings** too, or you will get way too much data in your sonar dashboard:

```python
DJANGO_SONAR = {
    'excludes': [
        STATIC_URL,
        MEDIA_URL,
        '/sonar/',
        '/admin/',
        '/__reload__/',
    ],
}
```

In this example I'm excluding all the http requests to static files, uploads, the sonar dashboard itself, the django admin panels and the browser reload library.
Update this setting accordingly, YMMW.

5. Now you should be able to execute the migrations to create the two tables that DjangoSonar will use to collect the data.

```bash
python manage.py migrate
```

6. And finally add the DjangoSonar middleware to your middlewares to enable the data collection:

```python
MIDDLEWARE = [
  ...
  'django_sonar.middlewares.requests.RequestsMiddleware',
  ...
]
```

## 😎 How to use

### The Dashboard

To access the dashboard you will point your browser to the /sonar/ url (but you can change it as described before). The interface is very simple and self explanatory.

You could use DjangoSonar in production too, since it gives you an historical overview of all the requests, but be sure to clear the data and disable it when you have debugged the problem.

🔔 If you forget to disable/clear DjangoSonar you could end up with several gigabytes of data collected. So please use it with caution when in production 🔔 

### sonar() - the dump helper

You can dump values to DjangoSonar using the **sonar()** helper function:

```python

from django_sonar.utils import sonar

sonar('something')

```

And you can also dump multiple values like this:

```python
from django_sonar.utils import sonar

sonar('something', self.request.GET, [1,2,3])
```


## ⚖️ License

DjangoSonar is open-sourced software licensed under the [MIT license](LICENSE.md).


## 🍺 Donations
If you really like this project and you want to help me please consider [buying me a beer 🍺](https://www.buymeacoffee.com/metalogico
) 
