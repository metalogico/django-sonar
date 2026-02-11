# DjangoSonar

The missing debug tool for django.

DjangoSonar is a comprehensive debugging and introspection tool for Django applications, inspired by Laravel Telescope.


<img width="1316" height="632" alt="image" src="https://github.com/user-attachments/assets/ccde5d44-47df-4c55-8463-f9508ec3157f" />



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
  - Events
  - Logs
  - (Signals coming soon™)
- Request insights:
  - Payload get/post
  - Auth User
  - Session vars
  - Headers
  - ...
- 🔒 Automatic sensitive data filtering (passwords, tokens, API keys, etc.)
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

### 🔒 Sensitive Data Protection

DjangoSonar automatically filters sensitive data from request payloads, headers, and session data before storing them in the database. By default, it masks common sensitive fields like:
- `password`, `passwd`, `pwd`, `pass`
- `token`, `api_key`, `secret`, `authorization`
- `credit_card`, `cvv`, `ssn`, `pin`
- And more...

These fields are replaced with `***FILTERED***` in the stored data.

**Custom Sensitive Fields**: You can add your own sensitive field patterns by adding them to the configuration:

```python
DJANGO_SONAR = {
    'excludes': [
        STATIC_URL,
        MEDIA_URL,
        '/sonar/',
    ],
    'sensitive_fields': [
        'custom_secret',
        'internal_api_key',
        'private_data',
    ],
}
```

The filtering is case-insensitive and works with partial matches (e.g., `user_password`, `my_api_key` will also be filtered).

### 💾 Separate Database Configuration (Recommended)

For better performance, it's recommended to store Django Sonar data in a separate database. This prevents monitoring overhead from impacting your main application database.

**Step 1**: Configure a separate database in your `settings.py`:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'your_main_db',
        # ... other settings
    },
    'sonar_db': {
        'ENGINE': 'django.db.backends.sqlite3',  # or postgresql, mysql, etc.
        'NAME': BASE_DIR / 'sonar.db',
    }
}
```

**Step 2**: Add the database router to your `settings.py`:

```python
DATABASE_ROUTERS = ['django_sonar.db_router.SonarDatabaseRouter']
```

**Step 3**: Run migrations:

```bash
# Migrate your main database (Django Sonar tables will be skipped)
python manage.py migrate

# Migrate the sonar database (only Django Sonar tables)
python manage.py migrate --database=sonar_db
```

Now all Django Sonar data will be stored in the separate database!

**Note**: The database router ensures that:
- Django Sonar tables **only** migrate to `sonar_db`
- Your main application tables **never** migrate to `sonar_db`
- Everything stays cleanly separated

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

**Only authenticated superusers can access sonar.** If you are trying to access the dashboard with a wrong type of user, you will see an error page, otherwise you should see the DjangoSonar login page.    

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

### Tracking events with `sonar_event()`

Use `sonar_event()` to push structured domain events into Sonar during a request:

```python
from django_sonar import sonar_event

sonar_event(
    'billing.invoice_paid',
    payload={'invoice_id': 123, 'amount': 49.90, 'currency': 'USD'},
    level='info',
    tags=['billing', 'payments'],
)
```

Tracked fields:
- `name`
- `level`
- `payload` (shown in the **Event Data** column)
- `tags`
- `timestamp`

These entries are shown in the **Events** panel.

### Tracking logs with `SonarHandler`

Attach `django_sonar.logging.SonarHandler` to Django logging to track log entries in Sonar:

```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {'class': 'logging.StreamHandler'},
        'sonar': {'class': 'django_sonar.logging.SonarHandler'},
    },
    'loggers': {
        '': {
            'handlers': ['console', 'sonar'],
            'level': 'INFO',
        },
    },
}
```

Example usage:

```python
import logging

logger = logging.getLogger(__name__)

logger.warning(
    'Payment retry scheduled',
    extra={
        'context': {'invoice_id': 123, 'attempt': 2},
        'queue': 'payments',
    },
)
```

Tracked fields:
- `logger`
- `level`
- `message`
- `context` (all extra fields are normalized into this)
- `timestamp`

These entries are shown in the **Logs** panel.

> Note: events/logs are buffered per request and persisted by the Sonar middleware at request end.

## 🧩 Custom Panels (For Developers)

DjangoSonar supports extension panels that are auto-registered from settings, so developers can add new dashboard sections without forking core views/templates.

### 1. Create a panel class

Create a module in your app, for example `myapp/sonar_panels.py`:

```python
from django_sonar.panels import SonarPanel


class EventsPanel(SonarPanel):
    key = 'events'
    label = 'Events'
    icon = 'bi-calendar-event'
    category = 'events'
    list_template = 'myapp/sonar/events_list.html'
    # optional:
    # detail_template = 'myapp/sonar/events_detail.html'
    # list_context_name = 'events'
```

Panel keys must be unique. Key collisions with built-ins or other custom panels raise an explicit configuration error.

### 2. Register your panel in settings

```python
DJANGO_SONAR = {
    'excludes': [
        STATIC_URL,
        MEDIA_URL,
        '/sonar/',
        '/admin/',
    ],
    'custom_panels': [
        'myapp.sonar_panels.EventsPanel',
    ],
}
```

### 3. Add the panel template

Create the template referenced by `list_template`, for example `myapp/templates/myapp/sonar/events_list.html`.

DjangoSonar renders this template at:

- `/sonar/p/events/` (list)
- `/sonar/p/events/<uuid>/` (detail, only if `detail_template` is defined)

The panel is also automatically shown in the Sonar sidebar navigation.

### 4. Store data under your panel category

Panel list queries use `SonarData.category` by default.  
For the example above, save entries with category `events` (for example via middleware/hooks/services) and they will appear in your custom panel.


## ⚖️ License

DjangoSonar is open-sourced software licensed under the [MIT license](LICENSE.md).


## 🍺 Donations
If you really like this project and you want to help me please consider [buying me a beer 🍺](https://www.buymeacoffee.com/metalogico
) 
