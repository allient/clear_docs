import hmac
import base64
import hashlib
import random
import string


class Helper(object):
    """Class used for helper functions"""

    @classmethod
    def get_secret_hash(cls, username, client_id, client_secret):
        """ Generate the secret hash needed for Cognito"""
        msg = username + client_id
        dig = hmac.new(str(client_secret).encode('utf-8'), msg=str(msg).encode('utf-8'), digestmod=hashlib.sha256).digest()
        return base64.b64encode(dig).decode()

    @classmethod
    def GenerateString(cls, p_Length=24, p_UrlFriendly=False):
        """Generate a random string

        Keyword Arguments:
            p_Length {int} -- This gives the lenght of the random string (default: {24})
            p_UrlFriendly {boolean} -- Set True this wil only return numbers and letters (default: {False})
        """

        rand = random.SystemRandom()
        if p_UrlFriendly:
            allowed_chars = string.ascii_letters + string.digits
        else:
            allowed_chars = string.ascii_letters + string.digits + string.punctuation

        # make sure we have always lower, upper and digits in the randomstring
        randomstring = random.choice(string.ascii_lowercase)
        randomstring += random.choice(string.ascii_uppercase)
        randomstring += random.choice(string.digits)

        for i in range(p_Length - 3):
            randomstring += random.choice(allowed_chars)

        random_list = list(randomstring)
        random.SystemRandom().shuffle(random_list)
        randomstring = ''.join(random_list)
        return randomstring