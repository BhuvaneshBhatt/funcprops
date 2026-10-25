"""Explicit bounded generation profiles, independent of machine speed."""

import os

from hypothesis import settings

settings.register_profile("ci", deadline=None, max_examples=50, derandomize=True)
settings.register_profile("extended", deadline=None, max_examples=250)
settings.load_profile(os.environ.get("FUNCPROPS_TEST_PROFILE", "ci"))
