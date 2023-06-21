{
    'name': 'Custody Clear Request',
    'version': '1.0',
    'summary': """
    This module allows you to request some amount and reconcile with specific expenses account or return as a cash, with dynamic 
    approval process for (Cash request/Cash Reconcile)
    """,
    'category': 'Accounting',
    'author': 'SGT',
    'support': 'support@softguidetech.com',
    'website': 'https://softguidetech.com',
    'license': 'OPL-1',
    'data': [

        'security/security_view.xml',
        'security/ir.model.access.csv',
        'views/custody_clear_request_view.xml',
        'views/custody_approval_route.xml',
        'views/res_config_settings_views.xml',
        'data/custody_approval_route.xml',
        'reports/custody_report.xml',
    ],
    'images': [
        'static/description/logo.png',
    ],
    'depends': ['base','account','analytic' ],




    'installable': True,
    'application': True,






}
