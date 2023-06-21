from odoo import models,fields,api,_

class PettycashReport(models.Model):
    _name = 'pettycash.report'

    company_id = fields.Many2one('res.company', string='Company')
    currency_id = fields.Many2one('res.currency', string='Currency')
    analytic_id = fields.Many2one('account.analytic.account',string='Analytic')
    request_id = fields.Many2one('custody.request',string='Petty cash request')
    request_clear_id = fields.Many2one('custody.clear.request',string='Petty cash request')
    user_id = fields.Many2one('res.users',string='User')
    amount = fields.Float(string='Balance')
    # request_date = fields.Date(string='Request Date')
    date = fields.Date(string=' Date')
