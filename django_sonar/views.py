import uuid

from django.shortcuts import render


def index(request):
    requests = [
        {
            'id': uuid.uuid4(),
            'method': 'GET',
            'url': 'https://example.com',
            'status': 200,
            'time': '2022-01-01 00:00:00'
        },
        {
            'id': uuid.uuid4(),
            'method': 'POST',
            'url': 'https://example.com',
            'status': 200,
            'time': '2022-01-01 00:00:00'
        },
        {
            'id': uuid.uuid4(),
            'method': 'PUT',
            'url': 'https://example.com',
            'status': 500,
            'time': '2022-01-01 00:00:00'
        }
    ]
    return render(request, 'django-sonar/requests/index.html',
                  {'requests': requests}
                  )
