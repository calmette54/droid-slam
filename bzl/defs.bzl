RevisionMode = provider(fields = ['type'])

revision_modes = ["RELEASE", "WIP", "DIRTY"]

def _revision_mode_impl(ctx):
    _revision_mode = ctx.build_setting_value
    if _revision_mode not in revision_modes:
        fail(str(ctx.label) + " build setting allowed to take values {"
             + ", ".join(revision_modes) + "} but was set to unallowed value "
             + _revision_mode)
    return RevisionMode(type = _revision_mode)

revision_mode = rule(
    implementation = _revision_mode_impl,
    build_setting = config.string(flag = True)
)
