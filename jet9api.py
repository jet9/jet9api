import os
import urllib2
import json
import tornado.escape
import tornado.ioloop
import tornado.web

from tornado.web import RequestHandler
from uuid import uuid4
from datetime import datetime, date

def validate_keys(_dict, mandatory_keys):
    """Check mandatory keys in dict"""

    for key in mandatory_keys:
        if key not in _dict.keys():
            return key

    return None


class Jet9APISever(object):
    def __init__(self, host="0.0.0.0", port=8888, mod_dir="actions"):
        self.host = host
        self.port = port
        self.mod_dir = mod_dir
        self.routes = []

        self._generate_routes()
        self.application = tornado.web.Application(self.routes)
        self.application.listen(self.port)

    def _import_actions(self):
        """ Import action modules from directory actions """

        mods = []
        for i in os.listdir("./%s/" % (self.mod_dir, )):
            if i.endswith(".py") and not i.startswith("__"):
                modname = i[:-3]
                #print mod_dir + "." + modname
                mods.append(__import__(self.mod_dir + "." + modname, fromlist=['action']))
                #action_mods.append(__import__(mod_dir + "." + modname))

        return mods

    def _generate_routes(self):
        """ Generate routes from action modules """

        route_template = r"/%s[/]*"
        routes = []

        for mod in self._import_actions():
            for action, cls in mod.action.items():
                self.routes.append(( route_template % (action, ), cls))

        return self.routes

    def run(self):
        tornado.ioloop.IOLoop.instance().start()

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


class Jet9APIError(Exception):
    pass

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


class Jet9APIRequest(object):
    def __init__(self, request):
        """Constructor"""

        key = validate_keys(request, ["uuid", "timestamp", "action", "params"])
        if key is None:
            self.timestamp = request["timestamp"]
            self.uuid = request["uuid"]
            self.action = request["action"]
            self.params = request["params"]
        else:
            raise Jet9APIError("Can't convert request: mandatory key [{0}] not found".format(key))

    def is_error(self):
        """Check wether request is error"""

        if self.code >= 300 and self.error is not None:
            return True

        return False

    def __str__(self):
        """Default str() returns raw request"""

        return self.raw

class Jet9APIRequestHandler(RequestHandler):
    __version__ = "1.0"

    def post(self):

        body = json.loads(str(self.request.body))
        result = self.process_action(body['action'], body)

        if isinstance(result, dict):
            self.write(self._wrap_response(result))

    def process_action(self, action, request):

        return getattr(self, "action_" + action)(request)

    def _wrap_response(self, result):
        result.update({
                        "uuid": str(uuid4()),
                        "version": self.__version__,
                        "timestamp": datetime.now().isoformat()
                    })

        return result

    def make_response(self, code, result):
        """ Make response to client """

        resp = {}
        if code < 300:
            if isinstance(result, dict):
                resp = {
                    "code": code,
                    "result": result,
                    "error": None
                }
            else:
                # XXX: make log record here
                resp = {
                    "code": 500,
                    "error": {
                        "message": "500 Internal Server Error 1"
                    },
                    "result": None
                }
        else:
            if isinstance(result, str):
                resp = {
                    "code": code,
                    "error": {
                        "message": result
                    },
                    "result": None,
                }
            else:
                # XXX: make log record here
                resp = {
                    "code": 500,
                    "error": {
                        "message": "500 Internal Server Error 2"
                    },
                    "result": None
                }

        return resp

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
