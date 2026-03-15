"""
elevate
~~~~

:copyright: (c) 2017-present by Justin Mayer.
:copyright: (c) 2014-2016 by Matt Robenolt.
:license: BSD, see LICENSE for more details.
"""

from importlib.metadata import PackageNotFoundError, version

try:
    VERSION = version("django-elevate")
except PackageNotFoundError:  # pragma: no cover
    VERSION = "unknown"
