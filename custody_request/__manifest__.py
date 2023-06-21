{
    'name': 'Custody Request',
    'version': '1.0',
    'author': 'Abdelwhab',
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
    'depends': ['base','account','analytic', 'check_followup','purchase'],




    'installable': True,
    'application': True,






}
