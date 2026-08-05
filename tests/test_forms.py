import unittest

from forms import BookForm


class BookFormTests(unittest.TestCase):
    def test_book_form_has_availability_field(self):
        form = BookForm()
        self.assertIn("availability", form._fields)


if __name__ == "__main__":
    unittest.main()
