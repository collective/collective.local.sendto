def v2(context):
    context.runImportStepFromProfile('profile-collective.local.sendto:default',
                                     'actions',
                                     run_dependencies=False, purge_old=False)

