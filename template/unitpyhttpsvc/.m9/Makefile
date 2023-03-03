# template: unitpyhttpsvc

runtime_path = .m9/runtime/$(M9_RUNTIME)

.PHONY : all init up down log re build dist deploy

cli = podman
pip_index = https://pypi.tuna.tsinghua.edu.cn/simple
apt_mirror= mirrors.tuna.tsinghua.edu.cn
image = python:3.10.7-slim
image_build = python:3.10.7

# https://github.com/nginx/unit/tree/master/pkg/docker
define IMAGECMD
FROM $(baseimage) as BUILDER
LABEL maintainer="NGINX Docker Maintainers <docker-maint@nginx.com>"
RUN set -ex \\
    && sed -i -e 's/deb.debian.org/$(apt_mirror)/g' /etc/apt/sources.list \\
    && apt-get update \\
    && apt-get install --no-install-recommends --no-install-suggests -y ca-certificates mercurial build-essential libssl-dev libpcre2-dev \\
    && mkdir -p /usr/lib/unit/modules /usr/lib/unit/debug-modules \\
    && hg clone https://hg.nginx.org/unit \\
    && cd unit \\
    && hg up 1.29.0 \\
    && NCPU="$$(getconf _NPROCESSORS_ONLN)" \\
    && DEB_HOST_MULTIARCH="$$(dpkg-architecture -q DEB_HOST_MULTIARCH)" \\
    && CC_OPT="$$(DEB_BUILD_MAINT_OPTIONS="hardening=+all,-pie" DEB_CFLAGS_MAINT_APPEND="-Wp,-D_FORTIFY_SOURCE=2 -fPIC" dpkg-buildflags --get CFLAGS)" \\
    && LD_OPT="$$(DEB_BUILD_MAINT_OPTIONS="hardening=+all,-pie" DEB_LDFLAGS_MAINT_APPEND="-Wl,--as-needed -pie" dpkg-buildflags --get LDFLAGS)" \\
    && CONFIGURE_ARGS="--prefix=/usr \\
                --state=/var/lib/unit \\
                --control=unix:/var/run/control.unit.sock \\
                --pid=/var/run/unit.pid \\
                --log=/var/log/unit.log \\
                --tmp=/var/tmp \\
                --user=unit \\
                --group=unit \\
                --openssl \\
                --libdir=/usr/lib/$$DEB_HOST_MULTIARCH" \\
    && ./configure $$CONFIGURE_ARGS --cc-opt="$$CC_OPT" --ld-opt="$$LD_OPT" --modules=/usr/lib/unit/debug-modules --debug \\
    && make -j $$NCPU unitd \\
    && install -pm755 build/unitd /usr/sbin/unitd-debug \\
    && make clean \\
    && ./configure $$CONFIGURE_ARGS --cc-opt="$$CC_OPT" --ld-opt="$$LD_OPT" --modules=/usr/lib/unit/modules \\
    && make -j $$NCPU unitd \\
    && install -pm755 build/unitd /usr/sbin/unitd \\
    && make clean \\
    && ./configure $$CONFIGURE_ARGS --cc-opt="$$CC_OPT" --modules=/usr/lib/unit/debug-modules --debug \\
    && ./configure python --config=/usr/local/bin/python3-config \\
    && make -j $$NCPU python3-install \\
    && make clean \\
    && ./configure $$CONFIGURE_ARGS --cc-opt="$$CC_OPT" --modules=/usr/lib/unit/modules \\
    && ./configure python --config=/usr/local/bin/python3-config \\
    && make -j $$NCPU python3-install \\
    && ldd /usr/sbin/unitd | awk '/=>/{print $$(NF-1)}' | while read n; do dpkg-query -S $$n; done | sed 's/^\([^:]\+\):.*$$/\\1/' | sort | uniq > /requirements.apt
FROM $(baseimage) as BASE
COPY entrypoint.sh /usr/local/bin/
COPY --from=BUILDER /usr/sbin/unitd /usr/sbin/unitd
COPY --from=BUILDER /usr/sbin/unitd-debug /usr/sbin/unitd-debug
COPY --from=BUILDER /usr/lib/unit/ /usr/lib/unit/
COPY --from=BUILDER /requirements.apt /requirements.apt
COPY --from=BUILDER /etc/apt/sources.list /etc/apt/sources.list
COPY requirements.txt /usr/etc/
RUN set -x \\
    && if [ -f "/tmp/libunit.a" ]; then \\
        mv /tmp/libunit.a /usr/lib/$$(dpkg-architecture -q DEB_HOST_MULTIARCH)/libunit.a; \\
        rm -f /tmp/libunit.a; \\
    fi \\
    && mkdir -p /var/lib/unit/ \\
    && mkdir /entrypoint.d/ \\
    && addgroup --system unit \\
    && adduser \\
         --system \\
         --disabled-login \\
         --ingroup unit \\
         --no-create-home \\
         --home /nonexistent \\
         --gecos "unit user" \\
         --shell /bin/false \\
         unit \\
    && apt update \\
    && apt --no-install-recommends --no-install-suggests -y install curl $$(cat /requirements.apt) \\
    && apt-get clean && rm -rf /var/lib/apt/lists/* \\
    && rm -f /requirements.apt \\
    && ln -sf /dev/stdout /var/log/unit.log \\
    && chmod +x /usr/local/bin/entrypoint.sh \\
    && pip3 install --index $(pip_index) -r /usr/etc/requirements.txt
STOPSIGNAL SIGTERM
WORKDIR /usr/src/
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
CMD ["unitd", "--no-daemon", "--control", "unix:/var/run/control.unit.sock"]
endef

define ENTRYPOINT
#!/bin/sh
set -e
WAITLOOPS=5
SLEEPSEC=1
curl_put()
{
    RET=$$(/usr/bin/curl -s -w '%{http_code}' -X PUT --data-binary @$$1 --unix-socket /var/run/control.unit.sock http://localhost/$$2)
    RET_BODY=$$(echo $$RET | /bin/sed '$$ s/...$$//')
    RET_STATUS=$$(echo $$RET | /usr/bin/tail -c 4)
    if [ "$$RET_STATUS" -ne "200" ]; then
        echo "$$0: Error: HTTP response status code is '$$RET_STATUS'"
        echo "$$RET_BODY"
        return 1
    else
        echo "$$0: OK: HTTP response status code is '$$RET_STATUS'"
        echo "$$RET_BODY"
    fi
    return 0
}
if [ "$$1" = "unitd" ] || [ "$$1" = "unitd-debug" ]; then
    if /usr/bin/find "/var/lib/unit/" -mindepth 1 -print -quit 2>/dev/null | /bin/grep -q .; then
        echo "$$0: /var/lib/unit/ is not empty, skipping initial configuration..."
    else
        if /usr/bin/find "/entrypoint.d/" -mindepth 1 -print -quit 2>/dev/null | /bin/grep -q .; then
            echo "$$0: /entrypoint.d/ is not empty, launching Unit daemon to perform initial configuration..."
            /usr/sbin/$$1 --control unix:/var/run/control.unit.sock

            while [ ! -S /var/run/control.unit.sock ]; do echo "$$0: Waiting for control socket to be created..."; /bin/sleep 0.1; done
            # even when the control socket exists, it does not mean unit has finished initialisation
            # this curl call will get a reply once unit is fully launched
            /usr/bin/curl -s -X GET --unix-socket /var/run/control.unit.sock http://localhost/

            echo "$$0: Looking for certificate bundles in /entrypoint.d/..."
            for f in $$(/usr/bin/find /entrypoint.d/ -type f -name "*.pem"); do
                echo "$$0: Uploading certificates bundle: $$f"
                curl_put $$f "certificates/$$(basename $$f .pem)"
            done

            echo "$$0: Looking for configuration snippets in /entrypoint.d/..."
            for f in $$(/usr/bin/find /entrypoint.d/ -type f -name "*.json"); do
                echo "$$0: Applying configuration $$f";
                curl_put $$f "config"
            done

            echo "$$0: Looking for shell scripts in /entrypoint.d/..."
            for f in $$(/usr/bin/find /entrypoint.d/ -type f -name "*.sh"); do
                echo "$$0: Launching $$f";
                "$$f"
            done

            # warn on filetypes we don't know what to do with
            for f in $$(/usr/bin/find /entrypoint.d/ -type f -not -name "*.sh" -not -name "*.json" -not -name "*.pem"); do
                echo "$$0: Ignoring $$f";
            done

            echo "$$0: Stopping Unit daemon after initial configuration..."
            kill -TERM $$(/bin/cat /var/run/unit.pid)

            for i in $$(/usr/bin/seq $$WAITLOOPS); do
                if [ -S /var/run/control.unit.sock ]; then
                    echo "$$0 Waiting for control socket to be removed..."
                    /bin/sleep $$SLEEPSEC
                else
                    break
                fi
            done
            if [ -S /var/run/control.unit.sock ]; then
                kill -KILL $$(/bin/cat /var/run/unit.pid)
                rm -f /var/run/control.unit.sock
            fi

            echo
            echo "$$0: Unit initial configuration complete; ready for start up..."
            echo
        else
            echo "$$0: /entrypoint.d/ is empty, skipping initial configuration..."
        fi
    fi
fi
exec "$$@"
endef

export ENTRYPOINT
export IMAGECMD

################################################################################

init: export baseimage=$(image)
init:
ifneq ($(and $(M9_RUNTIME),$(M9_PROJECT)),)
	@mkdir -p $(runtime_path)
	@echo "$$ENTRYPOINT" > $(runtime_path)/entrypoint.sh
	@echo "$$IMAGECMD" > $(runtime_path)/Dockerfile
	@cp requirements.txt $(runtime_path)
	@$(cli) build $(runtime_path) -t $(M9_PROJECT).$(M9_RUNTIME)
  ifneq ($(shell grep 'M9_PLACEHOLDER_port' unit/config.json),)
	@python -c "import socket; s=socket.socket(); s.bind(('', 0)); unp=s.getsockname()[1]; s.close(); \
    c=open('unit/config.json');r=c.read().replace('M9_PLACEHOLDER_port', str(unp));c.close(); \
	c=open('unit/config.json','w');c.write(r);c.close(); \
	print('default unit port is:', unp);"
  endif

endif

################################################################################

ifdef M9_ARGS_daemon
daemon = -d
else
daemon = --rm
endif

ifdef M9_ARGS_dryrun
up_mode = -it --entrypoint bash
else
up_mode = 
endif

ifneq ($(and $(ENV_host_port),$(ENV_unit_port)),)
net_mode = -p $(host_port):$(unit_port)
else
net_mode = --network host
endif

localmount =
ifneq (,$(wildcard asgi*))
localmount = -v ./:/usr/src/:Z
endif

env_file =
ifneq (,$(wildcard .env))
env_file = --env-file .env
endif

up:
ifdef M9_RUNTIME_FULLNAME
	$(cli)  run $(up_mode) $(daemon) $(net_mode) $(env_file) $(localmount) \
    -v ./unit/:/entrypoint.d/unit/:Z \
	-v /etc/localtime:/etc/localtime \
	--name=$(M9_RUNTIME_FULLNAME) $(M9_RUNTIME_FULLNAME)
endif

################################################################################

ifdef M9_ARGS_follow
log_mode = -f
else
log_mode = 
endif

log:
ifdef M9_RUNTIME_FULLNAME
	$(cli) logs $(log_mode) $(M9_RUNTIME_FULLNAME) 
endif

################################################################################

down:
ifdef M9_RUNTIME_FULLNAME
	$(cli) rm -f $(M9_RUNTIME_FULLNAME) 
endif

################################################################################

re:
ifdef M9_RUNTIME_FULLNAME
	$(cli) restart $(M9_RUNTIME_FULLNAME)
endif

################################################################################

build: export baseimage=$(image_build)
build:
	@mkdir -p ./build/
	@cp -rf $(runtime_path) ./build/
	@echo "$$IMAGECMD" > ./build/$(M9_RUNTIME)/Dockerfile
	@echo "\nnuitka\nordered-set" >> ./build/$(M9_RUNTIME)/requirements.txt
	@$(cli) build ./build/$(M9_RUNTIME) -t $(M9_PROJECT).$(M9_RUNTIME)_build 
	@$(cli) run --rm -v ./:/usr/src/:Z $(M9_PROJECT).$(M9_RUNTIME)_build python3 -m nuitka --module --include-module=asgi asgi

################################################################################

ifeq ($(M9_RUNTIME), default)
mkfile = Makefile
else
mkfile = Makefile.$(M9_RUNTIME)
endif

dist:
	@rm -rf ./dist && mkdir ./dist/

ifeq ($(M9_ARGS_distway), source)
	@cp -r asgi/ ./dist/
endif
ifeq ($(M9_ARGS_distway), binary)
	@cp ./asgi.*.so ./dist/
endif

ifdef M9_ARGS_distimage
	@echo "FROM localhost/$(M9_PROJECT).$(M9_RUNTIME)" > ./dist/Dockerfile
	@echo "ADD . /usr/src" >> ./dist/Dockerfile
	@$(cli) build ./dist/ -t $(M9_PROJECT).$(M9_RUNTIME)_distimage:$(M9_ARGS_distimage) >/dev/null
	@echo "image ready: $(M9_PROJECT).$(M9_RUNTIME)_distimage:$(M9_ARGS_distimage)"
	@rm -rf ./dist/*
	@$(cli) save -o ./dist/$(M9_PROJECT).$(M9_RUNTIME).$(M9_ARGS_distimage).tar --format oci-archive $(M9_PROJECT).$(M9_RUNTIME)_distimage:$(M9_ARGS_distimage)
endif
	@cp .env ./dist/.env
	@cp --parents .m9/meta.json .m9/$(mkfile) ./dist/
	@cp -r --parents .m9/runtime/$(M9_RUNTIME) ./dist/
	@cp --parents unit/config.json ./dist/
	@python -c "import json,datetime;c=open('./dist/.m9/meta.json'); r=json.load(c);c.close(); \
	r['project_dir']=None;r['dist_runtime']='$(M9_RUNTIME)';r['dist_way']='$(M9_ARGS_distway)';r['dist_image']='$(M9_ARGS_distimage)';r['dist_at']=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'); \
	c=open('./dist/.m9/meta.json','w');c.write(json.dumps(r));c.close()"

################################################################################

deploy:
ifndef M9_ARGS_distimage
	@$(cli) build $(runtime_path) -t $(M9_PROJECT).$(M9_RUNTIME)
	@cp -Trvf $(runtime_path) $(M9_ARGS_targetdir)/$(runtime_path) || :
  ifeq ($(M9_ARGS_distway), source)
	@cp -vfr ./asgi $(M9_ARGS_targetdir) || :
  endif
  ifeq ($(M9_ARGS_distway), binary)
	@cp -vf ./asgi.*.so $(M9_ARGS_targetdir) || :
  endif
else
	@([ -e $(M9_PROJECT).$(M9_RUNTIME).$(M9_ARGS_distimage).tar ] && $(cli) load -i $(M9_PROJECT).$(M9_RUNTIME).$(M9_ARGS_distimage).tar) || echo image file not found 
	@$(cli) tag $(M9_PROJECT).$(M9_RUNTIME)_distimage:$(M9_ARGS_distimage) $(M9_PROJECT).$(M9_RUNTIME):latest
endif
	@cp -vf .env $(M9_ARGS_targetdir) || :
	@cp -vf --parents .m9/$(mkfile) $(M9_ARGS_targetdir) || :
	@cp -vf --parents unit/config.json $(M9_ARGS_targetdir) || :

################################################################################
