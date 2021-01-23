from django.conf import settings

import os


def version(request):
    version = os.getenv("VERSION", "v0.0.0")

    if settings.DEBUG:
        version = "{version}-dev".format(version=version)

    return {"version": version}