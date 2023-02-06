#!/usr/bin/env python3
"""
9 looks like g
"""

import argparse
import logging
from logging.config import dictConfig
import sys
import os
import re
import shutil
import json
import datetime
import itertools
import subprocess
import textwrap

__version__ = "0.0.1"


#: The dictionary, passed to :class:`logging.config.dictConfig`,
#: is used to setup your logging formatters, handlers, and loggers
#: For details, see https://docs.python.org/3.4/library/logging.config.html#configuration-dictionary-schema
DEFAULT_LOGGING_DICT = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {"format": "[%(levelname)s] %(message)s"},
    },
    "handlers": {
        "default": {
            "level": "NOTSET",  # will be set later
            "formatter": "standard",
            "class": "logging.StreamHandler",
        },
    },
    "loggers": {
        __name__: {
            "handlers": ["default"],
            "level": "NOTSET",
            # 'propagate': True
        }
    },
}

M9PATH = os.path.join(os.path.expanduser("~"), ".m9/")
RELPATH_TPL_PROJ = "./template"
RELPATH_PROJECTS = "./projects"
RELPATH_RUNTIME = "./runtime"

ABSPATH_PROJECT = os.path.join(M9PATH, os.path.basename(RELPATH_PROJECTS))
ABSPATH_RUNTIME = os.path.join(M9PATH, os.path.basename(RELPATH_RUNTIME))
PROJECT_CONFIG = ".m9/project.json"

CURRENT_PATH = os.getcwd()
#: Map verbosity level (int) to log level
LOGLEVELS = {
    None: logging.WARNING,
    0: logging.ERROR,
    1: logging.WARNING,
    2: logging.INFO,
    3: logging.DEBUG,
}  # 0
#: Instantiate our logger
log = logging.getLogger(__name__)

#: Use best practice from Hitchhiker's Guide
#: see https://docs.python-guide.org/writing/logging/#logging-in-a-library
log.addHandler(logging.NullHandler())

IN_PROJECT = os.path.exists(".m9/meta.json")  # inside or outside of a m9 project folder ?


def get_m9_dir():
    if os.path.islink(__file__):
        return os.path.dirname(os.readlink(__file__))
    else:
        return os.path.dirname(__file__)


def get_tpl_path(rpth):
    return os.path.join(get_m9_dir(), os.path.relpath(rpth))


class m9util:
    def clean():
        for pn in os.listdir(ABSPATH_PROJECT):
            plink = os.path.join(ABSPATH_PROJECT, pn)
            if not os.path.exists(plink):
                os.remove(plink)
                for r in os.listdir(ABSPATH_RUNTIME):
                    if r.split(".")[0] == pn:
                        os.remove(os.path.join(ABSPATH_RUNTIME, r))
                log.warning(f"remove invalid project: {pn}")

        for rn in os.listdir(ABSPATH_RUNTIME):
            rf = os.path.join(ABSPATH_RUNTIME, rn)
            with open(rf) as f:
                rtmeta = json.load(f)
            if not os.path.exists(rtmeta['project_dir']):
                os.remove(rf)
                log.warning(f"remove invalid runtime: {rn}")

    def init_m9path():
        if not os.path.exists(M9PATH):
            os.makedirs(ABSPATH_PROJECT)
            os.makedirs(ABSPATH_RUNTIME)
            log.warning(f"m9 path inited at: {M9PATH}")

    def check_foldername(n):
        """checks for a valid foldername"""
        return bool(re.match(r"^[A-z0-9\-\_]+$", n))

    def check_tagname(n):
        """checks for a valid foldername"""
        return n.isalnum()

    def find_template(tn, rpth):
        """find template name in relative path"""

        rtpth = get_tpl_path(rpth)
        for _d in os.listdir(rtpth):
            log.debug(f"scanning: {_d}")
            if _d == tn:
                log.info(f"found template: {tn}")
                break
        else:
            return

        return os.path.join(rtpth, tn)

    def find_project(p, trypath=True):
        try:
            if p in os.listdir(ABSPATH_PROJECT):
                with open(os.path.join(ABSPATH_PROJECT, p)) as jfp:
                    return json.load(jfp)["project_dir"]
            if trypath and os.path.exists(os.path.join(p, ".m9/meta.json")):
                return os.path.abspath(p)

            return False
        except Exception as error:  # FIXME: add
            log.error(error)

    def find_runtime(rn):
        try:
            if rn in [r.rsplit(".", 1)[0] for r in os.listdir(ABSPATH_RUNTIME)]:
                return True

            return False
        except Exception as error:  # FIXME: add
            log.error(error)

    def load_project_commad(pth, cmd):
        with open(os.path.join(pth, PROJECT_CONFIG)) as jfp:
            for c in json.load(jfp)["commands"]:
                if c["name"] == cmd:
                    return c["args"]
            else:
                return

    def load_runtime_info(rn):
        try:
            with open(os.path.join(ABSPATH_RUNTIME, f"{rn}.json")) as jfp:
                return json.load(jfp)

        except Exception as error:  # FIXME: add
            log.error(error)

    def load_project_info(pth):
        try:
            with open(os.path.join(pth, ".m9/meta.json")) as jfp:
                return json.load(jfp)

        except Exception as error:  # FIXME: add
            log.error(error)


class m9:
    args = {}

    def build(project_abspath, runtime_fullname, args):
        project, runtime = runtime_fullname.split(".")
        env = dict(os.environ.copy(), **{"M9_RUNTIME": runtime, "M9_PROJECT": project})
        subprocess.run(args=args, cwd=project_abspath, env=env)

    def init(runtime, project_abspath, project, args):
        env = dict(os.environ.copy(), **{"M9_RUNTIME": runtime, "M9_PROJECT": project})
        subprocess.run(args=args, cwd=project_abspath, env=env)
        with open(os.path.join(ABSPATH_RUNTIME, f"{project}.{runtime}.json"), "w") as jfp:
            json.dump({"created_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "project_dir": project_abspath, "project": project}, jfp)
        log.debug(f"runtime created: {runtime} ")

    def up(rfn, pth, args, daemon, dryrun):
        env = os.environ.copy()
        env["M9_RUNTIME_FULLNAME"] = rfn
        if daemon:
            env["M9_ARGS_daemon"] = "true"
        if dryrun:
            env["M9_ARGS_dryrun"] = "true"

        try:
            subprocess.run(args=args, cwd=pth, env=env)
        except KeyboardInterrupt:
            log.warning("bye...")

    def down(rfn, pth, args):
        env = dict(os.environ.copy(), **{"M9_RUNTIME_FULLNAME": rfn})
        subprocess.run(args=args, cwd=pth, env=env)

    def re(rfn, pth, args):
        env = dict(os.environ.copy(), **{"M9_RUNTIME_FULLNAME": rfn})
        subprocess.run(args=args, cwd=pth, env=env)

    def log(rfn, pth, args, follow):
        env = dict(os.environ.copy(), **{"M9_RUNTIME_FULLNAME": rfn})
        if follow:
            env["M9_ARGS_follow"] = "true"
        try:
            subprocess.run(args=args, cwd=pth, env=env)
        except KeyboardInterrupt:
            log.warning("bye...")

    def new(proj_relpath, template_pth, overwrite=False):
        """create a new project folder here by copying project template"""
        if proj_relpath == ".":
            project = os.path.basename(CURRENT_PATH)
        else:
            project = proj_relpath
        proj_abspath = os.path.join(CURRENT_PATH, proj_relpath)

        plink = os.path.join(ABSPATH_PROJECT, project)
        if not overwrite and os.path.islink(plink):
            log.error(f"project name duplicated: {project}")
            return

        if os.path.exists(proj_abspath):
            pm9_abspath = os.path.join(proj_abspath, ".m9", "meta.json")
            if os.path.exists(pm9_abspath):
                log.error("project already exists here! ")
                return
            else:
                for root, dirs, files in os.walk(template_pth):
                    for d in itertools.chain(dirs, files):
                        if os.path.exists(os.path.join(proj_abspath, d)):
                            continue
                        if d in dirs:
                            shutil.copytree(os.path.join(root, d), os.path.join(proj_abspath, d))
                        else:
                            shutil.copyfile(os.path.join(root, d), os.path.join(proj_abspath, d))
                    break
        else:
            shutil.copytree(template_pth, proj_relpath, dirs_exist_ok=overwrite)

        meta = {
            "project": project,
            "project_dir": os.path.abspath(proj_abspath),
            "template": os.path.basename(template_pth),
            "created_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

        with open(f"{proj_relpath}/.m9/meta.json", "w") as jfp:
            json.dump(meta, jfp, indent=4)
            log.warning("meta.json created")

        try:
            os.symlink(os.path.abspath(f"{proj_relpath}/.m9/meta.json"), plink)
        except FileExistsError:
            if overwrite:
                os.remove(plink)
                os.symlink(os.path.abspath(f"{proj_relpath}/.m9/meta.json"), plink)

    def list(t):
        col = []
        for _t in t:
            _r = []
            match _t:
                case "p":
                    _r.extend(["PROJECT"])
                    _r.extend(sorted(os.listdir(ABSPATH_PROJECT)))
                case "t":
                    _r.extend(["TEMPLATE"])
                    _r.extend(sorted(os.listdir(get_tpl_path(RELPATH_TPL_PROJ))))
                case "r":
                    _r.extend(["RUNTIME"])
                    _r.extend(sorted(r.rsplit(".", 1)[0] for r in os.listdir(ABSPATH_RUNTIME)))  # remove .json extension
            col.append(_r)
        for r in itertools.zip_longest(*col, fillvalue=""):
            print("\t".join(["{0: <24}".format(str(_r)) for _r in r]))

    def show(proj_abspath):
        with open(os.path.join(proj_abspath, ".m9/meta.json")) as jfp:
            print(json.dumps(json.load(jfp), indent=4))

    def dist(proj_abspath, runtime, distimage, distway, args):
        env = os.environ.copy()
        env["M9_PROJECT"] = runtime.split(".")[0]
        env["M9_RUNTIME"] = runtime.split(".")[1]
        env["M9_ARGS_distway"] = distway

        if distimage:
            env["M9_ARGS_distimage"] = distimage

        subprocess.run(args=args, cwd=proj_abspath, env=env)

    def deploy(project, runtime, pack_relpath, distway, distimage, args):
        env = os.environ.copy()

        if not (target_dir := m9util.find_project(project, trypath=False)):  # create project object here
            print("deploying new project...")
            proj_abspath = os.path.abspath(os.path.join(CURRENT_PATH, pack_relpath))
            plink = os.path.join(ABSPATH_PROJECT, project)

            with open(f"{pack_relpath}/.m9/meta.json", "r+") as jfp:
                r = json.load(jfp)
                meta = {
                    "project": r["project"],
                    "project_dir": proj_abspath,
                    "template": r["template"],
                    "created_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                }
                jfp.seek(0)
                jfp.truncate()
                jfp.write(json.dumps(meta))

            os.symlink(f"{proj_abspath}/.m9/meta.json", plink)
            target_dir = proj_abspath

            if not m9util.find_runtime(f"{project}.{runtime}"):
                with open(os.path.join(ABSPATH_RUNTIME, f"{project}.{runtime}.json"), "w") as jfp:
                    json.dump({"created_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "project_dir": target_dir, "project": project}, jfp)

        env["M9_ARGS_targetdir"] = target_dir  # path to deply code
        env["M9_PROJECT"] = project
        env["M9_RUNTIME"] = runtime
        env["M9_ARGS_distway"] = distway
        env["M9_ARGS_distimage"] = distimage
        subprocess.run(args=args, cwd=pack_relpath, env=env)


class m9sd:
    tpl_unit_file = textwrap.dedent(
        """\
    [Unit]
    Description=

    [Service]
    Type=exec
    ExecStart=m9 up {rt}
    ExecStop=m9 down {rt}
    Restart=always
    RestartSec=0.9

    [Install]
    WantedBy=multi-user.target"""
    )
    SYSTEMD_UNIT_PATH = "/etc/systemd/system/"

    def __init__(self, action, runtimes):
        self.services = {f"{rt}.service": rt for rt in runtimes}

        all_installed_services = set(os.listdir(self.SYSTEMD_UNIT_PATH))

        self.uninstalled_m9_services = set(self.services.keys()) - all_installed_services
        self.installed_m9_services = set.intersection(all_installed_services, set(self.services.keys()))

        self.systemd(action)

    def systemd(self, action):
        getattr(self, "sd" + action)()

    def sdstatus(self):
        if not self.installed_m9_services:
            print("no services installed")
            return
        svcs = list(self.installed_m9_services)
        svcs.sort()
        data = [[self.services.get(r) for r in svcs]]
        for a in ["is-active", "is-enabled",]:
            r = subprocess.run(f"systemctl {a} {' '.join(svcs)}", shell=True, capture_output=True)
            data.append(r.stdout.decode().strip().split("\n"))

        print("\t".join(["{0: <24}".format(str(_r)) for _r in ["SERVICE", "IS-ACTIVE", "IS-ENABLED",]]))
        for r in itertools.zip_longest(*data):
            print("\t".join(["{0: <24}".format(str(_r)) for _r in r]))

    def sdinstall(self):
        for sv in self.uninstalled_m9_services:
            with open(self.SYSTEMD_UNIT_PATH + sv, "w") as fp:
                fp.write(self.tpl_unit_file.format(rt=self.services[sv]))

        os.system(f"systemctl enable {' '.join(self.services)}")
        os.system("systemctl daemon-reload")

        if self.installed_m9_services:
            print(f"services already installed:\n{' '.join(self.installed_m9_services)}")

    def sduninstall(self):
        for sv in self.installed_m9_services:
            os.remove(os.path.join(self.SYSTEMD_UNIT_PATH, sv))

        os.system(f"systemctl stop {' '.join(self.installed_m9_services)}")
        os.system(f"systemctl disable {' '.join(self.installed_m9_services)}")
        os.system("systemctl daemon-reload")
        if self.uninstalled_m9_services:
            print(f"services didn`t installed:\n{' '.join(self.uninstalled_m9_services)}")

    def sdstart(self):
        os.system(f"systemctl start {' '.join(self.installed_m9_services)}")
        if self.uninstalled_m9_services:
            print(f"services didn`t installed:\n{' '.join(self.uninstalled_services)}")

    def sdstop(self):
        os.system(f"systemctl stop {' '.join(self.installed_m9_services)}")
        if self.uninstalled_m9_services:
            print(f"services didn`t installed:\n{' '.join(self.uninstalled_m9_services)}")

    def sdrestart(self):
        os.system(f"systemctl restart {' '.join(self.installed_m9_services)}")
        if self.uninstalled_m9_services:
            print(f"services didn`t installed:\n{' '.join(self.uninstalled_m9_services)}")

    def sdenable(self):
        os.system(f"systemctl enable {' '.join(self.installed_m9_services)}")
        if self.uninstalled_m9_services:
            print(f"services didn`t installed:\n{' '.join(self.uninstalled_services)}")

    def sddisable(self):
        os.system(f"systemctl disable {' '.join(self.installed_m9_services)}")
        if self.uninstalled_m9_services:
            print(f"services didn`t installed:\n{' '.join(self.uninstalled_m9_services)}")


def parsecli(
    cliargs=None,
) -> argparse.Namespace:
    """Parse CLI with :class:`argparse.ArgumentParser` and return parsed result

    :param cliargs: Arguments to parse or None (=use sys.argv)
    :return: parsed CLI result
    """
    parser = argparse.ArgumentParser(description=__doc__, epilog="make it generated!")
    parser.add_argument("-v", "--verbose", action="count", default=0, help="increase verbosity level")
    parser.add_argument("--version", action="version", version="%(prog)s " + __version__)

    subparsers = parser.add_subparsers(required=True, dest="command")
    m9_show = subparsers.add_parser("show", help="show project info", usage="m9 show <project>|<path> ")
    m9_show.add_argument("project", help="project name or path")

    m9_list = subparsers.add_parser("list", help="list all", usage="m9 list <p|r|t>")
    m9_list.add_argument("-t", "--type", help="p: show project, r: show: runtime, t:show template", required=False)

    m9_new = subparsers.add_parser("new", help="create a new project in current directory", usage="m9 new <template> <project>")
    m9_new.add_argument("template", help="project template name")
    m9_new.add_argument("project", help="project name")
    m9_new.add_argument("-f", "--force", help="overwrite existed project", dest="overwrite", default=False, action="store_true")

    m9_init = subparsers.add_parser("init", help="init m9 runtime", usage="m9 init <runtime> <path>")
    m9_init.add_argument("runtime", help="runtime name")
    m9_init.add_argument("-p", "--proj", help="if provide a valid m9 project path, the dependencies would be installed to the runtime", dest="project", default=".")
    m9_init.add_argument("-f", "--force", help="overwrite existed runtime", dest="overwrite", default=False, action="store_true")

    m9_up = subparsers.add_parser("up", help="startup m9 runtime instance", usage="m9 up <RUNTIME>")
    m9_up.add_argument("runtime", help="runtime full name")
    m9_up.add_argument("-d", "--daemon", help="daemon mode", action="store_true", dest="daemon")
    m9_up.add_argument("--dry-run", help="ignore m9 project, just startup the runtime", action="store_true", dest="dryrun")
    m9_up.add_argument("-e", "--entry", help="specify the entry ", action="append", dest="entry")

    m9_log = subparsers.add_parser("down", help="ending runtime", usage="m9 down <RUNTIME>")
    m9_log.add_argument("runtime", help="runtime full name")

    m9_log = subparsers.add_parser("log", help="show runtime log", usage="m9 log <RUNTIME>")
    m9_log.add_argument("runtime", help="runtime full name")
    m9_log.add_argument("-f", "--follow", help="tail log", action="store_true", dest="follow")

    m9_log = subparsers.add_parser("re", help="restart full runtime", usage="m9 re <RUNTIME>")
    m9_log.add_argument("runtime", help="runtime full name")

    m9_build = subparsers.add_parser("build", help="build with runtime", usage="m9 build <project>|<path> <cmd> ...")
    m9_build.add_argument("runtime", help="runtime full name")

    m9_systemd = subparsers.add_parser("sd", help="systemd command sets", usage="m9 sd install|uninstall|enable|disable|start|stop|restart|status <runtime>")
    m9_systemd.add_argument("action", choices=["install", "uninstall", "enable", "disable", "start", "stop", "restart", "status"])
    m9_systemd.add_argument("runtime", nargs="+", help="runtime full name (`all` for every runtime)")

    m9_dist = subparsers.add_parser("dist", help="distribute runtime", usage="m9 dist <runtime> --image <DISTIMAGE TAG> -s | -b")
    m9_dist.add_argument("runtime", help="runtime full name")
    m9_dist.add_argument("-i", "--image", help="distribute container image", dest="distimage", required=False)
    g = m9_dist.add_mutually_exclusive_group(required=True)
    g.add_argument("-s", help="distribute as source", action="count")
    g.add_argument("-b", help="distribute as binary", action="count")

    m9_deploy = subparsers.add_parser("deploy", help="deploy distribution package", usage="m9 deploy <package> ...")
    m9_deploy.add_argument("package", help="distributed package folder")

    args = parser.parse_args(args=cliargs)
    return args


def proc(args):
    m9util.init_m9path()
    m9util.clean()
    match args.command:
        case "list":
            m9type = {
                "p",  # project
                "t",  # template
                "r",  # runtime
            }
            if not args.type:
                m9.list(["p", "r", "t"])
                return
            _args = set(args.type.lower())
            if _args.issubset(m9type):
                m9.list(list(_args))
            else:
                log.error("check your input of type")

        case "new":
            pn = args.project
            if pn != "." and not m9util.check_foldername(pn):
                log.error("check your project name")
                return

            if not (template_path := m9util.find_template(args.template, RELPATH_TPL_PROJ)):
                log.error(f"failed to find template: {args.template}")
                return

            m9.new(pn, template_path, args.overwrite)

        case "init":
            if not m9util.check_foldername(args.runtime):
                return log.error("check your runtime name")

            if m9util.find_runtime(args.runtime) and not args.overwrite:
                return log.error(f"runtime {args.runtime} already existed")

            if not (project_path := m9util.find_project(args.project)):
                return log.error("project not found")

            if not (_cmd := m9util.load_project_commad(project_path, "init")):
                return log.error("this project doesn`t supply init command")

            m9.init(args.runtime, project_path, os.path.basename(project_path), _cmd)

        case "up":
            if IN_PROJECT:
                rfn = f"{m9util.load_project_info('.')['project']}.{args.runtime.split('.')[-1]}"
            else:
                rfn = args.runtime

            if not (rtinfo := m9util.load_runtime_info(rfn)):
                return log.error("runtime not found")

            if not (_cmd := m9util.load_project_commad(rtinfo["project_dir"], "up")):
                return log.error("this project doesn`t supply up command")

            m9.up(rfn, rtinfo["project_dir"], _cmd, args.daemon, args.dryrun)

        case "log":
            if IN_PROJECT:
                rfn = f"{m9util.load_project_info('.')['project']}.{args.runtime.split('.')[-1]}"
            else:
                rfn = args.runtime

            if not (rtinfo := m9util.load_runtime_info(rfn)):
                return log.error("runtime not found")

            if not (_cmd := m9util.load_project_commad(rtinfo["project_dir"], "log")):
                return log.error("this project doesn`t supply log command")

            m9.log(rfn, rtinfo["project_dir"], _cmd, args.follow)

        case "down":
            if IN_PROJECT:
                rfn = f"{m9util.load_project_info('.')['project']}.{args.runtime.split('.')[-1]}"
            else:
                rfn = args.runtime

            if not (rtinfo := m9util.load_runtime_info(rfn)):
                return log.error("runtime not found")

            if not (_cmd := m9util.load_project_commad(rtinfo["project_dir"], "down")):
                return log.error("this project doesn`t supply down command")

            m9.down(rfn, rtinfo["project_dir"], _cmd)

        case "re":
            if IN_PROJECT:
                rfn = f"{m9util.load_project_info('.')['project']}.{args.runtime.split('.')[-1]}"
            else:
                rfn = args.runtime

            if not (rtinfo := m9util.load_runtime_info(rfn)):
                return log.error("runtime not found")

            if not (_cmd := m9util.load_project_commad(rtinfo["project_dir"], "re")):
                return log.error("this project doesn`t supply re command")

            m9.re(rfn, rtinfo["project_dir"], _cmd)

        case "build":
            if IN_PROJECT:
                rfn = f"{m9util.load_project_info('.')['project']}.{args.runtime.split('.')[-1]}"
            else:
                rfn = args.runtime

            if not (rtinfo := m9util.load_runtime_info(rfn)):
                return log.error("runtime not found")

            if not (_cmd := m9util.load_project_commad(rtinfo["project_dir"], "build")):
                return log.error("this project doesn`t supply build command")

            m9.build(rtinfo["project_dir"], rfn, _cmd)

        case "show":
            if not (project_path := m9util.find_project(args.project)):
                return log.error("project not found")

            m9.show(project_path)

        case "dist":

            if IN_PROJECT:
                rfn = f"{m9util.load_project_info('.')['project']}.{args.runtime.split('.')[-1]}"
            else:
                rfn = args.runtime

            if args.distimage and not m9util.check_tagname(args.distimage):
                return log.error("tag can only be composed of numbers and letters")

            if not (rtinfo := m9util.load_runtime_info(rfn)):
                return log.error("runtime not found")

            if not (_cmd := m9util.load_project_commad(rtinfo["project_dir"], "dist")):
                return log.error("this project doesn`t supply dist command")

            distway = None
            if args.s:
                distway = "source"
            if args.b:
                distway = "binary"
            if not distway:
                return log.error("missing distribute way")

            m9.dist(rtinfo["project_dir"], rfn, args.distimage, distway, _cmd)

        case "deploy":
            if not os.path.exists(args.package):
                return log.error("distribution package not found")

            if not (pinfo := m9util.load_project_info(args.package)):
                return log.error("invalid package")

            if "dist_runtime" not in pinfo:
                return log.error("invalid package info")

            print("package info:")
            [*map(print, pinfo.items())]

            if not (_cmd := m9util.load_project_commad(args.package, "deploy")):
                return log.error("this project doesn`t supply deploy command")

            m9.deploy(pinfo["project"], pinfo['dist_runtime'], args.package, pinfo['dist_way'], pinfo['dist_image'], _cmd)

        case "sd":
            all_runtime = [r.rsplit(".", 1)[0] for r in os.listdir(ABSPATH_RUNTIME)]
            if "all" in args.runtime:
                rts = all_runtime
            else:
                if wrts := set(args.runtime) - set(all_runtime):
                    return log.error(f"runtime not found: [{', '.join(wrts)}]")
                rts = args.runtime

            m9sd(args.action, rts)

        case _:
            pass


def main(cliargs=None) -> int:
    dictConfig(DEFAULT_LOGGING_DICT)

    try:
        args = parsecli(cliargs)
        proc(args)
        log.setLevel(LOGLEVELS.get(args.verbose, logging.INFO))
        log.debug("CLI result: %s", args)
        return 0

    # List possible exceptions here and return error codes
    except Exception as error:  # FIXME: add a more specific exception here!
        log.fatal(error)
        raise
        # Use whatever return code is appropriate for your specific exception
        return 10


if __name__ == "__main__":
    sys.exit(main())
