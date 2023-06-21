{
    'name': 'Custody Clear Request',
    'version': '1.0',
    'author': 'Abdelwhab Alim',
    'data': [

        'security/security_view.xml',
        'security/ir.model.access.csv',
        'views/custody_clear_request_view.xml',
        'views/custody_approval_route.xml',
        'views/res_config_settings_views.xml',
        'data/custody_approval_route.xml',
        'reports/custody_report.xml',
    ],
    'depends': ['base','account','analytic','custody_request'],




    'installable': True,
    'application': True,






}
