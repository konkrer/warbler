"""
User View tests.

# run these tests like:
#
#    python -m unittest test_user_views.py
"""

import os
from unittest import TestCase

from models import db, User, Message

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database
os.environ['DATABASE_URL'] = "postgresql:///warbler-test"

# formatter was moving this so...
if True:
    from app import app, CURR_USER_KEY

app.config['SQLALCHEMY_ECHO'] = False
app.config['TESTING'] = True
app.config['DEBUG_TB_HOSTS'] = ['dont-show-debug-toolbar']

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data
db.drop_all()
db.create_all()


app.config['WTF_CSRF_ENABLED'] = False


class UserViewsTestCase(TestCase):
    """Test User views including signup, login, logout."""

    def setUp(self):
        """Create test client, add sample data."""

        self.client = app.test_client()

        self.testuser = User.signup(username="testuser",
                                    email="test@test.com",
                                    password="testuser",
                                    image_url=None)

        self.testuser2 = User.signup(username="testuser2",
                                     email="test2@test.com",
                                     password="testuser2",
                                     image_url=None)
        db.session.commit()

        self.tu2_id = self.testuser2.id

    def tearDown(self):
        """Clean up any fouled transaction."""

        db.session.rollback()
        User.query.delete()

    def test_sign_up(self):
        """Can user sign up?"""

        data = {'username': "testuser3",
                'email': "test3@test.com",
                'password': "testuser3",
                'image_url': None
                }

        with self.client as c:
            resp = c.post("/signup", data=data)

        # Make sure it redirects
        self.assertEqual(resp.status_code, 302)

        user = User.query.filter_by(username='testuser3').one()
        self.assertEqual(user.email, "test3@test.com")

    def test_login(self):
        """Can user login?"""

        with self.client as c:
            resp = c.post(
                '/login', data={'username': 'testuser', 'password': 'testuser'}
            )

            self.assertEqual(resp.status_code, 302)

            with c.session_transaction() as sess:
                curr_logged_in_id = sess[CURR_USER_KEY]

            self.assertEqual(curr_logged_in_id, self.testuser.id)

    def test_logout(self):
        """Can user logout?"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.get('/logout')

            self.assertEqual(resp.status_code, 302)

            with c.session_transaction() as sess:
                curr_logged_in_id = sess.get(CURR_USER_KEY)

            self.assertEqual(curr_logged_in_id, None)

    def test_all_users_view(self):
        """Test all users are on users page."""

        with self.client as c:
            resp = c.get('/users')

            self.assertEqual(resp.status_code, 200)

            html = resp.get_data(as_text=True)
            self.assertIn('testuser', html)

    def test_user_detail_view(self):
        """Test user detail view."""

        msg = Message(user_id=self.testuser.id, text="Good day!")
        db.session.add(msg)
        db.session.commit()

        with self.client as c:
            resp = c.get(f'/users/{self.testuser.id}')

            self.assertEqual(resp.status_code, 200)

            html = resp.get_data(as_text=True)
            self.assertIn('testuser', html)
            self.assertIn('Good day!', html)

    def test_followers_view(self):
        """Test followers view. Should show those following user."""

        self.testuser2.following.append(self.testuser)
        db.session.commit()

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.get(f'/users/{self.testuser.id}/followers')

            self.assertEqual(resp.status_code, 200)

            html = resp.get_data(as_text=True)
            self.assertIn('testuser2', html)

    def test_followers_view_restricted(self):
        """Test followers view. Should show those following user."""

        with self.client as c:

            resp = c.get(f'/users/{self.testuser.id}/followers')

            self.assertEqual(resp.status_code, 302)

    def test_following_view(self):
        """Test following view. Should show those user is following."""

        self.testuser.following.append(self.testuser2)
        db.session.commit()

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.get(f'/users/{self.testuser.id}/following')

            self.assertEqual(resp.status_code, 200)

            html = resp.get_data(as_text=True)
            self.assertIn('testuser2', html)

    def test_following_view_restricted(self):
        """Test followers view. Should show those following user."""

        with self.client as c:

            resp = c.get(f'/users/{self.testuser.id}/following')

            self.assertEqual(resp.status_code, 302)

    def test_follow_user_view(self):
        """Test follow a user view."""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.post(
                f'/users/follow/{self.tu2_id}', follow_redirects=True)

            self.assertEqual(resp.status_code, 200)

            follows = User.query.get(self.testuser.id).following
            self.assertEqual(len(follows), 1)
            self.assertEqual(follows[0].id, self.tu2_id)

    def test_follow_user_view_restricted(self):
        """Test followers view. Should show those following user."""

        with self.client as c:

            resp = c.post('/users/follow/4')

            self.assertEqual(resp.status_code, 302)

    def test_stop_follow_user_view(self):
        """Test stop following a user view."""

        self.testuser.following.append(self.testuser2)
        db.session.commit()

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.post(
                f'/users/stop-following/{self.tu2_id}', follow_redirects=True)

            self.assertEqual(resp.status_code, 200)

            follows = User.query.get(self.testuser.id).following
            self.assertEqual(len(follows), 0)

    def test_stop_follow_user_view_restricted(self):
        """Test followers view. Should show those following user."""

        with self.client as c:

            resp = c.post('/users/stop-following/4')

            self.assertEqual(resp.status_code, 302)

    def test_edit_user_profile_view(self):
        """Test edit user profile view."""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.get('/users/profile')

            self.assertEqual(resp.status_code, 200)

            # make sure user data loaded into form.
            html = resp.get_data(as_text=True)
            self.assertIn('test@test.com', html)

            resp = c.post(
                '/users/profile', data={
                    'username': 'testuser',
                    'email': 'change@test.com',
                    'password': 'testuser'
                })

            self.assertEqual(resp.status_code, 302)

            tu = User.query.get(self.testuser.id)
            self.assertEqual(tu.email, 'change@test.com')

    def test_edit_user_view_restricted(self):
        """Test followers view. Should show those following user."""

        with self.client as c:

            resp = c.post('/users/profile')

            self.assertEqual(resp.status_code, 302)

    def test_delete_user_view(self):
        """Test delete user view."""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.post('/users/delete')

            self.assertEqual(resp.status_code, 302)

            self.assertRaises(
                Exception, db.session.query().get, self.testuser.id)

    def test_delete_user_view_restricted(self):
        """Test followers view. Should show those following user."""

        with self.client as c:

            resp = c.post('/users/delete')

            self.assertEqual(resp.status_code, 302)
