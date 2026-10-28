import unittest
from registration_app import default_login_destination

class DefaultLoginDestinationTests(unittest.TestCase):
    def test_personas_use_workspace(self):
        for role in ('iqs-registration-officer', 'iqs-verification-officer', 'iqs-programme-supervisor'):
            with self.subTest(role=role):
                self.assertEqual(default_login_destination('staff', [role]), '/registration/workspace')

    def test_reviewer_uses_protected_staff_page(self):
        self.assertEqual(default_login_destination('staff', ['iqs-intake-reviewer']), '/registration/staff')

    def test_beneficiary_and_unassigned(self):
        self.assertEqual(default_login_destination('beneficiary', []), '/registration/')
        self.assertEqual(default_login_destination('staff', []), '/registration/workspace')

if __name__ == '__main__':
    unittest.main()
