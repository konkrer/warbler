"""
Message View tests.

# run these tests like:
#
#    python -m unittest test_message_views.py
"""

import os
from unittest import TestCase

from models import db, Message, User

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


class MessageViewTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        self.client = app.test_client()

        self.testuser = User.signup(username="testuser",
                                    email="test@test.com",
                                    password="testuser",
                                    image_url=None)
        db.session.commit()

        self.new_message = Message(
            text="Hello I am a message.", user_id=self.testuser.id)

        db.session.add(self.new_message)
        db.session.commit()

        self.new_message_id = self.new_message.id

    def tearDown(self):
        """Clean up any fouled transaction."""

        db.session.rollback()
        User.query.delete()
        Message.query.delete()

    def test_add_message(self):
        """Can user add a message?"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.post("/messages/new", data={"text": "Hello"})

            # Make sure it redirects
            self.assertEqual(resp.status_code, 302)

            msg = Message.query.order_by(Message.id.desc()).first()

            self.assertEqual(len(User.query.one().messages), 2)
            self.assertEqual(msg.text, "Hello")

    def test_add_message_view_restricted(self):
        """Test user must be logged in to post message."""

        with self.client as c:

            resp = c.post('/messages/new')

            self.assertEqual(resp.status_code, 302)

    def test_show_message(self):
        """Can we view a message?"""
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            # remove logged in user to test general access
            with c.session_transaction() as sess:
                del sess[CURR_USER_KEY]

            resp = c.get(f'/messages/{self.new_message_id}')

            self.assertEqual(resp.status_code, 200)
            html = resp.get_data(as_text=True)
            self.assertIn("Hello I am a message.", html)

    def test_delete_message(self):
        """Can we delete a message"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.post(f'/messages/{self.new_message_id}/delete')

            self.assertEqual(resp.status_code, 302)

            msgs = Message.query.all()
            self.assertEqual(len(msgs), 0)
