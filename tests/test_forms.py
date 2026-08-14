import unittest

from flask import Flask

from forms import BookForm, LoginForm, RegistrationForm


class FormTests(unittest.TestCase):
    def setUp(self):
        # Flask-WTF forms need an application and request context to be built
        app = Flask(__name__)
        app.config.update(SECRET_KEY="test", WTF_CSRF_ENABLED=False)
        self.ctx = app.test_request_context()
        self.ctx.push()

    def tearDown(self):
        self.ctx.pop()

    def test_book_form_fields(self):
        form = BookForm()
        for name in ("title", "author", "genre", "description", "image", "rating", "security_deposit"):
            self.assertIn(name, form._fields)

    def test_book_form_does_not_expose_availability(self):
        # availability is managed by the borrow/return flow, not typed in by the owner
        self.assertNotIn("availability", BookForm()._fields)

    def test_login_form_has_remember_option(self):
        form = LoginForm()
        self.assertIn("remember", form._fields)
        self.assertFalse(form.remember.data)

    def test_registration_form_fields(self):
        form = RegistrationForm()
        for name in ("username", "city", "email", "password"):
            self.assertIn(name, form._fields)


if __name__ == "__main__":
    unittest.main()
