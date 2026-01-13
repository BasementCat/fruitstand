from app.lib.screen import Screen

from .view import bp


class ApprovalCode(Screen):
    key = "fruitstand/approval_code"
    title = "Approval Code"
    description = "Render an approval code to screens that are pending approval"
    blueprint = bp
    route = 'fruitstand_approvalcode.render'
    _is_system = True
