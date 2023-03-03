from sphinx import addnodes
from sphinx.domains.std import Cmdoption


def setup(app):
    app.add_directive("socon-admin-option", Cmdoption)
    app.add_crossref_type(
        directivename="setting",
        rolename="setting",
        indextemplate="pair: %s; setting",
    )
    app.add_object_type(
        directivename="socon-admin",
        rolename="socon-admin",
        indextemplate="pair: %s; socon command",
        parse_node=parse_socon_admin_command,
    )


def parse_socon_admin_command(env, sig, signode):
    command = sig.split(" ")[0]
    env.ref_context["std:program"] = command
    title = "socon %s" % sig
    signode += addnodes.desc_name(title, title)
    return command
