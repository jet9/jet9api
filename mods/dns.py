from jet9api.server import Jet9APIRequestHandler
from datetime import date

class DNSAction(Jet9APIRequestHandler):
    def action_list(self, request):
        resp = { "dns:request": request }
        code = 210

        return self.make_response(code, resp)

    def action_error_list(self, request):
        resp = "ERROR: some error here" 
        code = 400 

        return self.make_response(code, resp)

action = {
    "dns": DNSAction
}
