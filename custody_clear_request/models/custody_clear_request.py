from odoo import fields , models,api,tools,_
from datetime import datetime,timedelta
from odoo.exceptions import ValidationError
# from odoo import amount_to_text
from dateutil.relativedelta import relativedelta


class FinanceApprovalRequest(models.Model):
    _name = 'custody.clear.request'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Petty cash Reconcile Request'
    _order = 'custody_date desc'
    # def default_employee(self):
    #     return self.env.user.name

    def default_currency(self):
        return self.env.user.company_id.currency_id

    @api.depends('amount','currency_id')
    def _onchange_amount(self):
        from ..models.money_to_text_ar import amount_to_text_arabic
        if self.amount:
            self.num2wo = amount_to_text_arabic(
                self.amount, self.env.user.company_id.currency_id.name)

    def default_company(self):
        return self.env.user.company_id

    def default_user_analytic(self):
        return self.env.user

    @api.returns('self')
    def _default_employee_get(self):
        return self.env.user

    # def manager_default(self):
    #     return self.env.user.manager_id

    name = fields.Char('Reference',readonly=True,default='New',copy=False)
    description = fields.Char('Description',)
    user_name = fields.Many2one('res.users', string='User Name',readonly=True, default=_default_employee_get)
    # manager_id = fields.Many2one('res.users','Manager',default=manager_default)

    custody_date = fields.Date('Reconcile Date', default=lambda self: fields.Date.today(), track_visibility='onchange')
    currency_id = fields.Many2one('res.currency', string='Currency',default=default_currency,required=True)
    amount = fields.Monetary('Reconcile Amount', track_visibility='onchange')
    sequence = fields.Integer(required=True, default=1,)
    state = fields.Selection([('draft','Draft'),
                              ('dm','Submitted'),
                              ('am','Confirmed'),
                              ('fm','Approved'),
                              ('post','Posted'),
                              ('cancel','Cancel')],default='draft',track_visibility='onchange')
    num2wo = fields.Char('Amount In Text',compute='_onchange_amount',store=True)
    company_id = fields.Many2one('res.company',string="Company Name",default=default_company)

    # Accounting Fields
    total_amount_ex = fields.Float('Total Amount',readonly=True)
    custody_ids = fields.One2many('custody.request','custody_clear_id',string="Petty cash Request")
    total_history_amount = fields.Monetary('Total Hostory Amount',readonly=True,compute='com_total_history')
    move_id = fields.Many2one('account.move',string='Expense entry',readonly=True,copy=False)
    journal_id = fields.Many2one('account.journal',string='Diff Journal', domain="[('type','in',['cash','bank'])]")
    custody_journal_id = fields.Many2one('account.journal',string='Expense Journal')
    journal_type = fields.Selection(related='journal_id.type')
    # partner_id = fields.Many2one('res.partner',string="Employee")
    # employee_name = fields.Many2one('res.partner', string="Employee Name",domain="[('is_employee','=',True)]")
    account_id = fields.Many2one('account.account',compute='_account_compute',string='Petty cash account')
    total_tax = fields.Float('Tax',compute='_compute_tax')
    total_with_ex = fields.Float('Subtotal',compute='_total_with_ex')
    total = fields.Float('Total Expense',compute='_total_expense')

    count_je = fields.Integer(compute='_count_je_compute')
    count_diff = fields.Integer(compute='_count_diff_compute')
    request_id = fields.Many2one('custody.request',string='Petty cash Request',domain=[('state','=','post')])
    total_request_amount = fields.Float(compute='_get_request_total')
    attachment = fields.Binary(string='Attachments / المرفقات')
    notes = fields.Text(string='Notes / ملاحظات ')


    @api.onchange('custody_line_ids')
    def _onchange_amount(self):
        # for rec in self:
        total = 0
        for i in self.custody_line_ids:
            total += i.amount
        self.amount = total

    def approval_message(self):
        self.message_post(body=_("Cash Reconcile Request need approval %s" % self.name),
                          message_type='comment',
                          subtype_xmlid='mail.mt_note',
                          author_id=self.user_name.partner_id.id)


    @api.depends('user_name')
    def _account_compute(self):
        setting_ob = self.env['res.config.settings'].search([], order='id desc', limit=1)
        print('aaaaaaaaaaaaaaaaaaa', setting_ob)
        if setting_ob.petty_account_id:
            self.account_id = setting_ob.petty_account_id
        if not self.company_id.petty_account_id:
            raise ValidationError('Please Insert Petty cash account In Company Configuration')
        else:
            self.account_id = self.company_id.petty_account_id
    @api.depends('request_id')
    def _get_request_total(self):
      self.total_request_amount=0
      if self.request_id:
          self.total_request_amount=self.request_id.amount

    def _count_je_compute(self):
        for i in self:
            if i.move_id:
                i.count_je = 1
            else:
                i.count_je = 0

    def _count_diff_compute(self):
        for i in self:
            if i.move_id2:
                i.count_diff = 1
            else:
                i.count_diff = 0

    def action_move(self):
        tree_view = self.env.ref('account.view_move_tree')
        form_view = self.env.ref('account.view_move_form')
        return {
            'type': 'ir.actions.act_window',
            'name': 'View Journal Entry',
            'res_model': 'account.move',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'views': [(tree_view.id, 'tree'), (form_view.id, 'form')],
            'domain': [('id', '=', self.move_id.id)],

        }

    def action_move_diff(self):
        tree_view = self.env.ref('account.view_move_tree')
        form_view = self.env.ref('account.view_move_form')
        return {
            'type': 'ir.actions.act_window',
            'name': 'View Journal Entry',
            'res_model': 'account.move',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'views': [(tree_view.id, 'tree'), (form_view.id, 'form')],
            'domain': [('id', '=', self.move_id2.id)],

        }

    # @api.one
    @api.depends('custody_line_ids')
    def _total_with_ex(self):
        total_without = 0
        for i in self.custody_line_ids:
            total_without += i.amount
        self.total_with_ex = total_without

    @api.depends('custody_line_ids')
    def _compute_tax(self):
        total =0
        for i in self.custody_line_ids:
            total += i.tax_amount
        self.total_tax = total

    @api.depends('custody_line_ids')
    def _total_expense(self):
        # total_tax = 0
        total_am = 0
        for i in self.custody_line_ids:
            # total_tax += i.tax_amount
            total_am += i.amount
        self.total = total_am

    @api.depends('user_name')
    def _compute_account(self):
        setting_ob = self.env['res.config.settings'].search([], order='id desc', limit=1)


        if setting_ob.petty_account_id:
            self.account_id = setting_ob.petty_account_id
        if not self.company_id.petty_account_id:
            raise ValidationError('Please Insert Petty cash account In Company Configuration')
        else:
            self.account_id = self.company_id.petty_account_id

    user_id = fields.Many2one('res.users', default=default_user_analytic)
    # analytic_account = fields.Many2one(related='user_id.analytic_account_id', string='Analytic Account')

    # analytic_account = fields.Many2one('account.analytic.account',string='Analytic Account')
    check_term = fields.Selection([('not_followup','Not Follow-up'),
                                   ('followup','Follow-up')
                                   ],
                                  default='not_followup',invisible=True)

    # clrarance Line Many2one
    custody_line_ids = fields.One2many('custody.clear.line','custody_request_id',string='Expenses Line',copy=True)
    # Check Details
    check_date = fields.Date('Check Date',)
    check_number = fields.Char('Check Number')
    bank_template = fields.Many2one('res.bank')
    check_id = fields.Many2one('check.followup',string="Check Reference",readonly=True)

    move_id2 = fields.Many2one('account.move',string='Difference Move',readonly=True)

    def users_fm(self):
        users_obj = self.env['res.users']
        users = []
        for user in users_obj.search([]):
            if user.has_group("custody_clear_request.group_custody_clear_fm"):
                users.append(user.id)
        return users

    def confirm_dm(self):
        if not self.custody_line_ids:
            raise ValidationError("Please add expense lines !!")
        if self.amount <= 0:
            raise ValidationError("Please Make Sure Amount Field Grater Than Zero !!")

        if not self.custody_line_ids:
            raise ValidationError("Please Insert at Least One Line Expense")
        if self.env.user.name != self.user_id.name:
            raise ValidationError("Please This Request is not For You")
        if not self.custody_line_ids:
            raise ValidationError("Please Insert Columns in ")
        else:
            user_fm_ids = self.env['res.users'].search([('id','in',self.users_fm())])
            channel_group_obj = self.env['mail.mail']
            partner_list = []
            for rec in user_fm_ids:
                partner_list.append(rec.partner_id.id)
            receipt_ids = self.env['res.partner'].search([('id', 'in', partner_list)])
            dic = {
                'subject': _('Cash Reconcile Need Approval: %s') % (self.name,),
                'email_from': self.user_name.login,
                'body_html': 'Hello, Please approve petty cash Reconcile with number ' + self.name,
                'recipient_ids': receipt_ids.ids,
            }
            mail = channel_group_obj.create(dic)
            mail.send()
            self.write({'state': 'dm'})

        # self.description = 'Petty cash reconcile for account' + ' ' + str(self.account_id.name)

    def confirm_am(self):

        self.write({'state': 'am'})


    def confirm_fm(self):
        # if self.check_term == 'followup' and self.journal_type != 'bank':
        #     raise ValidationError("Please Don't Filling Check Information")
        # else:
        for i in self.custody_line_ids:
            if not i.account_id:
                raise ValidationError('Please insert expense accounts !!')
        self.write({'state': 'fm'})
        if not self.account_id or not self.custody_journal_id:
            raise ValidationError("Please Fill Accounting information (Journal-Employee-Account)")
        if self.check_term == 'followup':
            if not self.check_number or not self.check_date or not self.bank_template:
                raise ValidationError("Please Fill Check Details !!")
    @api.model
    def get_amount(self):
        for i in self.custody_line_ids:
            if self.amount > self.total_amount_ex:
                if i.currency_id != self.env.user.company_id.currency_id:
                    return i.amount * self.env.user.company_id.currency_id.rate
                if i.currency_id == self.env.user.company_id.currency_id:
                    return i.amount

            if self.amount < self.total_amount_ex:
                if i.currency_id != self.env.user.company_id.currency_id:
                    return i.amount / i.currency_id.rate
                if i.currency_id == self.env.user.company_id.currency_id:
                    return i.amount

            if self.amount == self.total_amount_ex:
                if i.currency_id != self.env.user.company_id.currency_id:
                    return i.amount / i.currency_id.rate
                if i.currency_id == self.env.user.company_id.currency_id:
                    return i.amount

    @api.model
    def get_amount_general(self):
        for i in self.custody_line_ids:
            if self.amount > self.total_amount_ex:
                if i.currency_id != self.env.user.company_id.currency_id:
                    return i.amount / i.currency_id.rate
                if i.currency_id == self.env.user.company_id.currency_id:
                    return i.amount

            if self.amount < self.total_amount_ex:
                if i.currency_id != self.env.user.company_id.currency_id:
                    return i.amount / i.currency_id.rate
                if i.currency_id == self.env.user.company_id.currency_id:
                    return i.amount

            if self.amount == self.total_amount_ex:
                if i.currency_id != self.env.user.company_id.currency_id:
                    return i.amount / i.currency_id.rate
                if i.currency_id == self.env.user.company_id.currency_id:
                    return i.amount


    @api.model
    def get_currency(self):
        for i in self.custody_line_ids:
            if i.currency_id != self.env.user.company_id.currency_id:
                return i.currency_id.id
            else:
                return i.currency_id.id

    @api.model
    def amount_currency_debit(self):
        for i in self.custody_line_ids:
            if i.currency_id != self.env.user.company_id.currency_id:
                return i.amount
            else:
                return i.amount
    @api.model
    def amount_currency_tax_debit(self):
        for i in self.custody_line_ids:
            if i.currency_id != self.env.user.company_id.currency_id:
                return i.tax_amount
            else:
                return i.tax_amount

    @api.model
    def amount_currency_credit(self):
        for i in self.custody_line_ids:
            if i.currency_id != self.env.user.company_id.currency_id:
                return i.amount * -1
            else:
                return i.amount

    @api.model
    def amount_currency_credit_equal(self):
        for i in self.custody_line_ids:
            if i.currency_id != self.env.user.company_id.currency_id:
                return self.amount * -1
            else:
                return self.amount

    @api.model
    def get_total_credit_amount_ex(self):
        for i in self.custody_line_ids:
            if i.currency_id != self.env.user.company_id.currency_id:
                return self.total_amount_ex * -1
            else:
                return self.total_amount_ex

    @api.model
    def get_totaporl_debit_amount_ex(self):
        for i in self.custody_line_ids:
            if i.currency_id != self.env.user.company_id.currency_id:
                return self.total_amount_ex
            else:
                return self.total_amount_ex

    # @api.onchange('user_name')
    @api.depends('custody_ids','user_name')
    def com_total_history(self):
        if self.user_name:
            serach_custody = self.env['custody.request'].search([('user_name','=',self.user_name.name),
                                                                 ('state','=','post')])
            search_custody_clear = self.env['custody.clear.request'].search([('user_name','=',self.user_name.name),
                                                                             ('state','=','post')])
            print("USsssssssssssss",serach_custody)
            total_custody =0
            total_clear = 0
            total_amount = 0
            total_tax = 0
            for c in search_custody_clear:
                total_clear += c.amount

            print('cccccccccc',total_clear)
            for i in serach_custody:
                total_custody += i.amount
            print('ppppppppppp',total_custody)
            self.total_history_amount = total_custody - total_clear

    def confirm_post(self):
        l = []
        account_move_object = self.env['account.move']
        if not self.account_id or not self.custody_journal_id:
            raise ValidationError("Please Make Sure Partner Accounting Tab was Entered or Journal !!")
        for rec in self.custody_line_ids:
            if not rec.account_id:
                raise ValidationError('Please insert Expense account in Expense lines !!')
        credit_amount = self.amount
        credit_curr_amount = self.amount * -1
        if self.currency_id != self.env.user.company_id.currency_id:
            credit_amount = self.amount * self.env.user.company_id.currency_id.rate
            currency_id = self.currency_id.id
            credit_curr_amount = self.amount
        if self.currency_id == self.env.user.company_id.currency_id:
            credit_amount = self.amount
            currency_id = self.currency_id.id
            credit_curr_amount = self.amount * -1
        credit_val = {

            'move_id': self.move_id.id,
            'name': 'Petty cash reconcile for account' + ' ' + str(self.account_id.name),
            'account_id': self.account_id.id,
            'credit': credit_amount,
            'currency_id': self.currency_id.id,
            'partner_id': self.user_name.partner_id.id,
            'amount_currency': credit_curr_amount,
            # # 'analytic_account_id': ,
            # 'company_id': self.company_id.id or False,

        }
        l.append((0, 0, credit_val))

        curr_amount = 0
        amount = 0
        for i in self.custody_line_ids:
            description = i.name
            if i.currency_id != self.env.user.company_id.currency_id:
                amount = i.amount * self.env.user.company_id.currency_id.rate
                curr_amount = i.amount
            if i.currency_id == self.env.user.company_id.currency_id:
                amount = i.amount
                curr_amount = i.amount
            debit_val = {
                'move_id': self.move_id.id,
                'name': description,
                'account_id': i.account_id.id,
                'debit': amount,
                # 'analytic_distribution': i.analytic_accont_id.id or False,
                'currency_id': self.currency_id.id,
                # 'partner_id': self.user_name.partner_id.id,
                'amount_currency': curr_amount or False,
                # 'company_id': self.company_id.id or False,

            }
            l.append((0, 0, debit_val))
            if i.tax_amount:
                if not i.tax_id.account_id:
                    raise ValidationError('Please insert debit account in tax configuration')
                if i.currency_id != self.env.user.company_id.currency_id:
                    tax = i.tax_amount / i.currency_id.rate
                    tax_amount = i.tax_amount
                if i.currency_id == self.env.user.company_id.currency_id:
                    tax = i.tax_amount / i.currency_id.rate
                    tax_amount = i.tax_amount
                debit_val2 = {
                    'move_id': self.move_id.id,
                    'name': 'Tax of petty cash expense',
                    'account_id': i.tax_id.account_id.id,
                    'debit': tax,
                    # 'analytic_distribution': i.analytic_accont_id.id or False,
                    'currency_id': self.currency_id.id,
                    # 'partner_id': self.user_name.partner_id.id,
                    'amount_currency': tax_amount or False,
                    # 'company_id': self.company_id.id or False,

                }
                l.append((0, 0, debit_val2)) or False

        print("List", l)
        vals = {
            'journal_id': self.custody_journal_id.id,
            'date': self.custody_date,
            'ref': str(self.user_name.partner_id.name) + str(' / ') + str(self.name),
            # 'company_id': ,
            'line_ids': l,
        }
        self.move_id = account_move_object.create(vals)
        self.move_id.action_post()

        channel_group_obj = self.env['mail.mail']
        partner_list = []
        for rec in self.user_name:
            partner_list.append(rec.partner_id.id)
        receipt_ids = self.env['res.partner'].search([('id', 'in', partner_list)])
        dic = {
            'subject': _('Cash Reconcile Approved: %s') % (self.name,),
            'email_from': self.env.user.login,
            'body_html': 'Hello, Approved petty cash Reconcile with number ' + self.name,
            'recipient_ids': partner_list,
        }
        mail = channel_group_obj.create(dic)
        mail.send()

        self.state = 'done'

###############################################################
        report_ob = self.env['pettycash.report']
        for e in self.custody_line_ids:
            report_vals ={
                'company_id': e.company_id.id,
                'currency_id': e.currency_id.id,
                'user_id': e.user_id.id,
                'amount': (e.amount + e.tax_amount) * -1,
                'analytic_id': e.analytic_accont_id.id,
                'request_clear_id': e.custody_request_id.id,
                'date': self.custody_date,
            }
            report_ob.sudo().create(report_vals)
        if self.total != self.amount:
            amount = (self.amount - self.total)
            report_vals2 = {
                'company_id': self.company_id.id,
                'currency_id': self.currency_id.id,
                'user_id': self.user_name.id,
                'amount': amount * -1,
                # 'analytic_id': e.analytic_accont_id.id,
                'request_clear_id': self.id,
                'date': self.custody_date,

            }
            report_ob.sudo().create(report_vals2)
###############################################################

    def tax_debit(self):
        for i in self.custody_line_ids:
            if i.currency_id != self.env.user.company_id.currency_id:
                return i.tax_amount / i.currency_id.rate
            else:
                return i.tax_amount

    def difference_debit(self):
        for i in self.custody_line_ids:
            if i.currency_id != self.env.user.company_id.currency_id:
                diff = self.amount - self.total
                return diff / self.currency_id.rate
            else:
                return self.amount - self.total

    def amount_currency_debit_difference2(self):
        for i in self.custody_line_ids:
            if i.currency_id != self.env.user.company_id.currency_id:
                return self.total - self.amount

    def amount_currency_credit_difference2(self):
        return (self.total - self.amount) * -1

    def difference_debit2(self):
        for i in self.custody_line_ids:
            if i.currency_id != self.env.user.company_id.currency_id:
                diff = self.total - self.amount
                return diff / self.currency_id.rate
            else:
                return self.total - self.amount

    def total_credit(self):
        for i in self.custody_line_ids:
            if i.currency_id != self.env.user.company_id.currency_id:
                return self.total / self.currency_id.rate
            else:
                return self.total

    def total_debit(self):
        for i in self.custody_line_ids:
            if i.currency_id != self.env.user.company_id.currency_id:
                return i.amount

    def amount_debit(self):
        for i in self.custody_line_ids:
            if i.currency_id != self.env.user.company_id.currency_id:
                return i.amount / i.currency_id.rate
            else:
                return i.amount

    def amount_currency_debit_difference(self):
        for i in self.custody_line_ids:
            if i.currency_id != self.env.user.company_id.currency_id:
                return self.amount - self.total

    def amount_currency_credit_diffrence(self):
        for i in self.custody_line_ids:
            if i.currency_id != self.env.user.company_id.currency_id:
                diff = self.amount - self.total
                return diff * -1

    def amount_currency_total(self):
        for i in self.custody_line_ids:
            if i.currency_id != self.env.user.company_id.currency_id:
                return self.total * -1

    @api.model
    def create(self, vals):
        code = 'custody.clear.request.code'

        if vals.get('name', 'New') == 'New':
            message = 'Reconcile' + self.env['ir.sequence'].next_by_code(code)
            vals['name'] = message
            # self.message_post(subject='Create CCR', body='This is New CCR Number' + str(message))
        return super(FinanceApprovalRequest, self).create(vals)

    # @api.multi
    def unlink(self):
        for i in self:
            if i.state != 'draft':
                raise ValidationError("Please Make Sure State in DRAFT !!")
            else:
                super(FinanceApprovalRequest, i).unlink()

    # def copy(self):
    #     raise ValidationError("Can not Duplicate a Record !!")

    def cancel_request(self):

        self.move_id.button_cancel()
        self.move_id.unlink()
        channel_group_obj = self.env['mail.mail']
        partner_list = []
        for rec in self.user_name:
            partner_list.append(rec.partner_id.id)
        receipt_ids = self.env['res.partner'].search([('id', 'in', partner_list)])
        dic = {
            'subject': _('Cash Reconcile Canceled: %s') % (self.name,),
            'email_from': self.env.user.login,
            'body_html': 'Hello, Canceled petty cash Reconcile with number ' + self.name,
            'recipient_ids': partner_list,
        }
        mail = channel_group_obj.create(dic)
        mail.send()
        self.state = 'cancel'

    def reject(self):
        for i in self.approver_ids:
            i.unlink()
        self.state = 'draft'


class CustodyClearLine(models.Model):
    _name = 'custody.clear.line'

    def _default_user(self):
        return self.env.user.id

    def _default_date(self):
        return self.custody_request_id.custody_date

    def _default_name(self):
        return self.product_id.name

    name = fields.Char('Label',related='product_id.name')
    doc_attachment_id = fields.Many2many('ir.attachment', 'doc_attach_rel2', 'doc_id', 'attach_id3', string="Attachment",
                                         help='You can attach the copy of your document', copy=False)
    analytic_accont_id = fields.Many2one('account.analytic.account',string='Analytic account', track_visibility='onchange')
    amount = fields.Float('Amount',required=True)
    custody_request_id = fields.Many2one('custody.clear.request',string='Petty cash')
    account_id = fields.Many2one('account.account',string='Expense Account')
    #############
    currency_id = fields.Many2one('res.currency','Currency',compute='_compute_currency')
    company_id = fields.Many2one('res.company','Company',compute='_compute_company')
    user_id = fields.Many2one('res.users','User',compute='_compute_user')
    date_clear = fields.Date(string='Clear Date',compute='_compute_date')
    # analytic_id = fields.Many2one('account.analytic.account',compute='_compute_analytic')
    #############
    state = fields.Selection(related='custody_request_id.state')
    user_name = fields.Many2one(related='custody_request_id.user_name')
    # user_id = fields.Many2one('res.users',default=_default_user)
    tax_id = fields.Many2one('account.tax', string='Tax', domain="[('type_tax_use','=','purchase')]")
    tax_amount = fields.Float('Tax amount')
    date = fields.Date('Date',required=True,related='custody_request_id.custody_date')
    product_id = fields.Many2one('product.product',string='Product',required=True)
    partner_id = fields.Many2one('res.partner',string='Vendor')

    @api.onchange('product_id')
    def _onchange_account(self):
        if self.product_id:
            self.account_id = self.product_id.property_account_expense_id.id

    @api.depends('custody_request_id.currency_id')
    def _compute_currency(self):
        self.currency_id = self.custody_request_id.currency_id
    ######################3

    @api.depends('custody_request_id.company_id')
    def _compute_company(self):
        self.company_id = self.custody_request_id.company_id

    @api.depends('custody_request_id.user_name')
    def _compute_user(self):
        self.user_id = self.custody_request_id.user_name

    @api.depends('custody_request_id.custody_date')
    def _compute_date(self):
        self.date_clear = self.custody_request_id.custody_date

    @api.onchange('tax_id')
    def _tax_amount_compute(self):
        if self.tax_id and self.amount:
            if self.tax_id.amount_type == 'percent':
                self.tax_amount = (self.amount * self.tax_id.amount) / 100
            if self.tax_id.amount_type == 'fixed':
                self.tax_amount = self.tax_id.amount


class ClearRequestInherit(models.Model):
    _inherit = 'custody.request'

    clear_ids = fields.One2many('custody.clear.request','request_id',string='Reconcile Request')
    clear_num = fields.Integer(compute="_compute_clear_num")

    def _compute_clear_num(self):
        search_clear_ids = self.env['custody.clear.request'].search_count([('request_id','=',self.id)])
        self.clear_num = search_clear_ids

    def action_reconcile_request(self):
        search_clear_ids = self.env['custody.clear.request'].search([('request_id','=',self.id)])
        lis = []
        for i in search_clear_ids:
            lis.append(i.id)
        tree_view = self.env.ref('custody_clear_request.custody_clear_request_tree')
        form_view = self.env.ref('custody_clear_request.custody_clear_request_form')
        return {
            'type': 'ir.actions.act_window',
            'name': 'View Reconcile Request',
            'res_model': 'custody.clear.request',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'views': [(tree_view.id, 'tree'), (form_view.id, 'form')],
            'domain': [('id', 'in', lis)],

        }
