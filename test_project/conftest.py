import os

# pytest-playwright runs inside an async event loop, which triggers Django's
# async safety check on ORM calls. Allow synchronous ORM usage in tests.
os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"
