import urllib2
import json

from uuid import uuid4
from datetime import datetime

def validate_keys(_dict, mandatory_keys):
    """Check mandatory keys in dict"""

    for key in mandatory_keys:
        if key not in _dict.keys():
            return key

    return None

class Jet9APIError(Exception):
    pass

class Jet9APIResponse(object):
    def __init__(self, response):
        """Constructor"""

        if isinstance(response, str):
            self.raw = response
            try:
                response = json.loads(response)
            except:
                raise Jet9APIError("Can't convert response: Response is not a JSON")

        key = validate_keys(response, ["version", "uuid", "timestamp", "result", "code", "error"])
        if key is None:
            self.version = response["version"]
            self.uuid = response["uuid"]
            self.timestamp = response["timestamp"]
            self.result = response["result"]
            self.code = response["code"]
            self.error = response["error"]
        else:
            raise Jet9APIError("Can't convert response: mandatory key [{0}] not found".format(key))

    def is_error(self):
        """Check wether response is error"""

        if self.code >= 300 and self.error is not None:
            return True

        return False

    def __str__(self):
        """Default str() returns raw response"""

        return self.raw

class Jet9APIClient(object):
    """ Jet9 API interaction class """

    def __init__(self, host, authtoken):
        """ Constructor """

        self.host = host

        if host.startswith("https://"):
            self.ssl = True
        elif host.startswith("http://"):
            self.ssl = False
        else:
            raise Jet9APIError("Invalid host: should be http(s)://")

        self.authtoken = authtoken

    def request(self, subsystem, action, params):
        """ Do API request """

        data = {
            "authtoken": self.authtoken,
            "action": action,
            "params": params,
        }

        request = urllib2.Request(url=self.host+"/"+subsystem, data=json.dumps(data))

        return Jet9APIResponse(urllib2.urlopen(request).read())



if __name__ == "__main__":
    j = Jet9APIClient(host="http://127.0.0.1:8888", authtoken="AUTHTOKEN")

    params = {
        "domain": "orfiq.com",
        "limit": 20,
    }

    try:
        res = j.request("dns", "error_list", params)
        if not res.is_error():
            print "code:", res.code
            print "result:", res.result
        else:
            print "code:", res.code
            print "error:", res.error["message"]
        
        print j.request("dns", "error_list", params)

    except urllib2.HTTPError as e:
        print "ERROR: {0}".format(str(e))
