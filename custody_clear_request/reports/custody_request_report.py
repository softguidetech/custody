from odoo import models,fields,api,_

class FinanceApprovalReport(models.AbstractModel):
    _name = 'custody.clear.request.report'

    @api.model
    def render_html(self, docids, data=None):
        report_obj = self.env['report']
        report = report_obj._get_report_from_name('custody_clear_request.report_custody')
        docargs = {
            'doc_ids': docids,
            'doc_model': report.custody.clear.request,
            'docs': self,
        }
        return report_obj.render('custody_clear_request.report_custody', docargs)