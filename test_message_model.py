"""Message model tests."""

# run these tests like:
#
#    python -m unittest test_message_model.py


import os
from unittest import TestCase
from datetime import datetime

from models import db, User, Message

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


class MessageModelTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        self.testuser = User.signup(username="testuser",
                                    email="test@test.com",
                                    password="testuser",
                                    image_url=None)
        db.session.commit()

        self.message = Message(user_id=self.testuser.id,
                               text="Distant horizon.")
        db.session.add(self.message)
        db.session.commit()

        self.client = app.test_client()

    def tearDown(self):
        db.session.rollback()
        User.query.delete()
        Message.query.delete()

    def test_user_model(self):
        """Does basic model work?"""

        self.assertEqual(len(self.testuser.messages), 1)
        self.assertEqual(self.message.user, self.testuser)
        self.assertIsInstance(self.message.timestamp, datetime)
        self.assertEqual(self.message.text, "Distant horizon.")
