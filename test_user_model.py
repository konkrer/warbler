"""User model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py


import os
from unittest import TestCase

from models import db, User, Message, Follows

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"

# Now we can import app
if True:
    from app import app

app.config['SQLALCHEMY_ECHO'] = False
app.config['TESTING'] = True
app.config['DEBUG_TB_HOSTS'] = ['dont-show-debug-toolbar']

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data
db.drop_all()
db.create_all()


class UserModelTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        self.testuser = User.signup(username="testuser",
                                    email="test@test.com",
                                    password="testuser",
                                    image_url=None)

        self.testuser2 = User.signup(username="testuser2",
                                     email="test2@test.com",
                                     password="testuser2",
                                     image_url=None)
        db.session.commit()

        self.tu1_id = self.testuser.id
        self.tu2_id = self.testuser2.id

        self.client = app.test_client()

    #
    def tearDown(self):
        db.session.rollback()
        User.query.delete()
        Message.query.delete()
        Follows.query.delete()

    #
    def test_user_model(self):
        """Does basic model work?"""

        # User should have no messages & no followers
        self.assertEqual(len(self.testuser.messages), 0)
        self.assertEqual(len(self.testuser.followers), 0)
        self.assertEqual(len(self.testuser.likes), 0)

    #
    def test_is_following_true(self):
        """Test is_following function returns true for following."""

        follow = Follows(user_being_followed_id=self.tu2_id,
                         user_following_id=self.tu1_id)
        db.session.add(follow)
        db.session.commit()

        self.assertTrue(self.testuser.is_following(
            self.testuser2))

    #
    def test_is_following_false(self):
        """Test is_following function returns false for not following."""

        self.assertFalse(self.testuser.is_following(
            User.query.get(self.tu2_id)))

    #
    def test_is_followed_by_true(self):
        """Test is_followed_by function returns true when followed."""

        follow = Follows(user_being_followed_id=self.tu2_id,
                         user_following_id=self.tu1_id)
        db.session.add(follow)
        db.session.commit()

        self.assertTrue(self.testuser2.is_followed_by(
            self.testuser))

    #
    def test_is_followed_by_false(self):
        """Test is_followed_by function returns false when not followed."""

        self.assertFalse(self.testuser2.is_followed_by(
            self.testuser))

    #
    def test_user_signup_valid(self):
        """Test signup function returns user when valid."""

        new_user = User.signup(username='testuser9', email='abc@test.com',
                               password='holy_cow', image_url=None)

        self.assertIsInstance(new_user, User)
        self.assertEqual(new_user.username, 'testuser9')

    #
    def test_user_signup_invalid(self):
        """Test signup function raises error when invalid."""

        User.signup(username='testuser', email='abc@test.com',
                    password='holy_cow', image_url=None)

        self.assertRaises(Exception, db.session.commit)

        db.session.rollback()

        User.signup(username='testuser9', email='test@test.com',
                    password='holy_cow', image_url=None)

        self.assertRaises(Exception, db.session.commit)

    #
    def test_user_authenticate_valid(self):
        """Test authenticate function returns user when valid."""

        user = User.authenticate(username='testuser',
                                 password='testuser')

        self.assertIsInstance(user, User)
        self.assertEqual(user.username, 'testuser')

    #
    def test_user_authenticate_invalid_username(self):
        """Test authenticate function raises error when invalid username."""

        user = User.authenticate(username='testuser9',
                                 password='testuser')
        self.assertFalse(user)

    #
    def test_user_authenticate_invalid_password(self):
        """Test authenticate function raises error when invalid password."""

        user = User.authenticate(username='testuser',
                                 password='testuser9')
        self.assertFalse(user)

    #
    def test_user_repr(self):
        """Test User repr returns desired string."""

        desired_repr = \
            f'<User #{self.tu1_id}: {self.testuser.username}, {self.testuser.email}>'  # NOQA E501

        self.assertEqual(self.testuser.__repr__(), desired_repr)
