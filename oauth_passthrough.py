import base64
import cgi
import json
import urllib

# TODO: mention http://www-cs-students.stanford.edu/~tjw/jsbn
from Crypto.Cipher import PKCS1_OAEP
from Crypto.PublicKey import RSA

CLIENT_ID = "alexa-skill"
KEY_FILENAME = "oauth_passthrough.key.pub"
REDIRECT_URI = "Redirect URI for the OAuth client"

class RedirectException(Exception):
    pass

def assert_event_okay(event):
    """Make sure that the given event is valid.

    As an OAuth provider, we should check that the client_id and redirect_uri
    are okay. Since these are hardcoded for us, the check is easy. Also, we
    only support implicit grants, so that check is easy too.
    """
    assert event["client_id"] == CLIENT_ID
    assert event["redirect_uri"] == REDIRECT_URI
    assert event["response_type"] == "token"

class EventHandler(object):
    """A class that contains functions to generate responses to an event.

    This exists primarily so we don't need to keep passing the event's contents
    around a whole bunch. We could instead have decided to pass the event
    around, but prefer this because we can more explicitly extract certain
    fields of interest.
    """
    def __init__(self, event):
        self.client_id = event["client_id"]
        self.email = event.get("email", "")
        self.password = event.get("password")
        self.redirect_uri = event["redirect_uri"]
        self.response_type = event["response_type"]
        self.scope = event.get("scope", "")
        self.state = event["state"]

    def request_password_page(self, error=None):
        """Returns the HTML for a page that will ask for email and password."""
        # TODO: Make use of "error".
        # TODO: add styling
        return """
<!DOCTYPE html>
<html>
  <head>
    <meta charset="UTF-8">
    <title>title</title>
  </head>
  <body>
    <form>
      Email Address:<br>
      <input id="email" type="email" name="email" value="{email}"><br>
      Password:<br>
      <input id="password" type="password" name="password"><br>
      <input type="hidden" name="client_id" value="{client_id}">
      <input type="hidden" name="redirect_uri" value="{redirect_uri}">
      <input type="hidden" name="response_type" value="{response_type}">
      <input type="hidden" name="scope" value="{scope}">
      <input type="hidden" name="state" value="{state}">
      <input type="submit">
    </form>
  </body>
</html>
        """.format(
            email=cgi.escape(self.email),
            client_id=cgi.escape(self.client_id),
            redirect_uri=cgi.escape(self.redirect_uri),
            response_type=cgi.escape(self.response_type),
            scope=cgi.escape(self.scope),
            state=cgi.escape(self.state)
        )

    def redirect(self, encryption_key):
        """Throws an exception that indicates we should redirect.

        This is built to work around AWS' API Gateway's limitations. We want to
        be able to serve both 200s and 302s, but API Gateway only allow one type
        of response code on success. So to serve both 200s and 302s, we need to
        throw an exception for at least one of these, and we choose to do this
        for 302s.

        The next limitation is that when a lambda function throws exceptions, it
        returns a dictionary like
        {
            stackTrace: [],
            errorType: "",
            errorMessage: ""
        }
        so in order to pass the redirect url along, we need to fit it into one
        of these. The API Gateway allows us to read these fields, but not do
        post processing. So we make the error message be exactly the url we
        want.
        """
        # TODO: make sure email and password aren't url encoded.
        cipher = PKCS1_OAEP.new(encryption_key)
        token = json.dumps({"email": self.email, "password": self.password})
        encrypted_token = cipher.encrypt(token)
        # url encoding can handle the encrypted token, but b64 encoding it makes
        # it short and arguably nicer to read
        encoded_encrypted_token = base64.b64encode(encrypted_token)
        fragment = urllib.urlencode({
            "state": self.state,
            "token_type": "bearer",
            "access_token": encoded_encrypted_token
        })
        url = REDIRECT_URI + "#" + fragment
        raise RedirectException(url)

def validate_email_and_password(email, password):
    # TODO: Add actual validation
    return True

def main(event, context):
    assert_event_okay(event)
    handler = EventHandler(event)
    email = event.get("email", "")
    password = event.get("password", "")
    if validate_email_and_password(email, password):
        key = RSA.importKey(open(KEY_FILENAME).read())
        # This actually raises, but we leave the return statement since the
        # raise is acting like a return.
        return handler.redirect(key)
    return handler.request_password_page(error=None)
