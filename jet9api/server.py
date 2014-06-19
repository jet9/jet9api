import os
import json

import tornado.ioloop
from tornado.web import RequestHandler, Application

from uuid import uuid4
from datetime import datetime, date
from jet9api.client import validate_keys, Jet9APIError

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

class Jet9APISever(object):
    def __init__(self, host="0.0.0.0", port=8888, mod_dir="actions"):
        self.host = host
        self.port = port
        self.mod_dir = mod_dir
        self.routes = []

        self._generate_routes()
        self.application = Application(self.routes)
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
