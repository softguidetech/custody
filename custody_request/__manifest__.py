{
    'name': 'Custody Request',
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
    'price': '35',
    'currency': 'EUR',
    'data': [

        'security/security_view.xml',
        'security/ir.model.access.csv',
        'views/custody_request_view.xml',
        'views/configure_view.xml',
        'data/custody_approval_route.xml',
        'views/custody_approval_route.xml',
        'views/res_config_settings_views.xml',
        'reports/custody_report.xml',
    ],
    'images': [
        'static/description/logo.png',
    ],
    'depends': ['base','account','analytic','custody_clear_request'],




    'installable': True,
    'application': True,






}
