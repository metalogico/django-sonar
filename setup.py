from setuptools import setup, find_packages

setup(
    name='django_sonar',
    version='0.1.0',  # Start with a suitable version number for your project
    author='Metalogico',
    author_email='michele.brandolin@gmail.com',  # Replace with your email
    description='The missing debug tool for Django',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/metalogico/django-sonar',
    project_urls={
        "Bug Tracker": "https://github.com/metalogico/django-sonar/issues"
    },
    license='MIT',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'Django>=4.0',
    ],
    classifiers=[
        'Development Status :: 3 - Alpha',  # Change as appropriate
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',  # Ensure this matches your chosen license
        'Operating System :: OS Independent',
        'Framework :: Django',
        'Framework :: Django :: 4.0',
        'Framework :: Django :: 5.0',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
    ],
    python_requires='>=3.8',
)
