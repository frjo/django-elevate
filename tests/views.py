from django.template.response import TemplateResponse

from elevate.forms import ElevateForm
from elevate.settings import REDIRECT_FIELD_NAME, REDIRECT_TO_FIELD_NAME, REDIRECT_URL
from elevate.views import (
    elevate,
    redirect_to_elevate,
)

from .base import BaseTestCase


class ElevateViewTestCase(BaseTestCase):
    def test_enforces_logged_in(self):
        response = elevate(self.request)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], "/accounts/login/?next=/foo")

    def test_returns_template_response(self):
        self.login()
        self.request.is_elevated = lambda: False
        response = elevate(self.request)
        self.assertIsInstance(response, TemplateResponse)
        self.assertEqual(response.template_name, "elevate/elevate.html")  # default
        self.assertEqual(
            response.context_data[REDIRECT_FIELD_NAME], REDIRECT_URL
        )  # default
        form = response.context_data["form"]
        self.assertIsInstance(form, ElevateForm)
        self.assertEqual(form.user, self.user)
        self.assertEqual(form.request, self.request)

    def test_returns_template_response_with_next(self):
        self.login()
        self.request.GET = {REDIRECT_FIELD_NAME: "/lol"}
        self.request.is_elevated = lambda: False
        response = elevate(self.request)
        self.assertEqual(response.context_data[REDIRECT_FIELD_NAME], "/lol")  # default

    def test_returns_template_response_override_template(self):
        self.login()
        self.request.is_elevated = lambda: False
        response = elevate(self.request, template_name="foo.html")
        self.assertEqual(response.template_name, "foo.html")

    def test_returns_template_response_override_extra_context(self):
        self.login()
        self.request.is_elevated = lambda: False
        response = elevate(self.request, extra_context={"foo": "bar"})
        self.assertEqual(response.context_data["foo"], "bar")

    def test_redirect_if_already_elevated(self):
        self.login()
        self.request.is_elevated = lambda: True
        response = elevate(self.request)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], REDIRECT_URL)

    def test_redirect_fix_bad_url(self):
        self.login()
        self.request.is_elevated = lambda: True
        self.request.GET = {REDIRECT_FIELD_NAME: "http://mattrobenolt.com/lol"}
        response = elevate(self.request)
        self.assertEqual(response["Location"], REDIRECT_URL)
        self.request.GET = {
            REDIRECT_FIELD_NAME: "http://%s\\@mattrobenolt.com"
            % self.request.get_host(),
        }
        response = elevate(self.request)
        self.assertEqual(response["Location"], REDIRECT_URL)

    def test_redirect_if_already_elevated_with_next(self):
        self.login()
        self.request.GET = {REDIRECT_FIELD_NAME: "/lol"}
        self.request.is_elevated = lambda: True
        response = elevate(self.request)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], "/lol")

    def test_redirect_after_successful_post(self):
        self.login()
        self.request.is_elevated = lambda: False
        self.request.method = "POST"
        self.request.csrf_processing_done = True
        self.request.POST = {"password": "foo"}
        response = elevate(self.request)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], REDIRECT_URL)

    def test_session_based_redirect(self):
        self.login()
        self.request.is_elevated = lambda: False
        self.request.method = "GET"
        self.request.GET = {REDIRECT_FIELD_NAME: "/foobar"}
        elevate(self.request)

        self.request, self.request.session = self.post("/foo"), self.request.session
        self.login()
        self.request.is_elevated = lambda: False
        self.request.method = "POST"
        self.request.POST = {"password": "foo"}
        self.request.csrf_processing_done = True
        response = elevate(self.request)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], "/foobar")
        self.assertNotEqual(response["Location"], REDIRECT_URL)
        self.assertFalse("redirect_to" in self.request.session)

    def test_session_based_redirect_bad_url(self):
        self.login()
        self.request.is_elevated = lambda: False
        self.request.method = "POST"
        self.request.POST = {"password": "foo"}
        self.request.session[REDIRECT_TO_FIELD_NAME] = "http://mattrobenolt.com/lol"
        self.request.csrf_processing_done = True
        response = elevate(self.request)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], REDIRECT_URL)
        self.assertFalse("redirect_to" in self.request.session)
        self.request.session[REDIRECT_TO_FIELD_NAME] = (
            "http://%s\\@mattrobenolt.com" % self.request.get_host()
        )
        response = elevate(self.request)
        self.assertEqual(response["Location"], REDIRECT_URL)

    def test_render_form_with_bad_password(self):
        self.login()
        self.request.is_elevated = lambda: False
        self.request.method = "POST"
        self.request.csrf_processing_done = True
        self.request.POST = {"password": "lol"}
        response = elevate(self.request)
        self.assertEqual(response.status_code, 200)
        form = response.context_data["form"]
        self.assertFalse(form.is_valid())


class RedirectToElevateTestCase(BaseTestCase):
    def test_redirect_to_elevate_simple(self):
        response = redirect_to_elevate("/foo")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], "/elevate/?next=/foo")

    def test_redirect_to_elevate_with_querystring(self):
        response = redirect_to_elevate("/foo?foo=bar")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], "/elevate/?next=/foo%3Ffoo%3Dbar")

    def test_redirect_to_elevate_custom_url(self):
        response = redirect_to_elevate("/foo", "/lolelevate/")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], "/lolelevate/?next=/foo")
