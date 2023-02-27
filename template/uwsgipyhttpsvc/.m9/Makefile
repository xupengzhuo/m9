# template: uwsgipyhttpsvc

runtime_path = .m9/runtime/$(M9_RUNTIME)

.PHONY : all init up down log re build dist deploy

cli = podman
pip_index = https://pypi.tuna.tsinghua.edu.cn/simple
apt_mirror= mirrors.tuna.tsinghua.edu.cn
image = python:3.10-slim
image_build = python:3.10


define IMAGECMD
FROM $(baseimage) as BUILDER
RUN set -ex \\
	&& sed -i -e 's/deb.debian.org/$(apt_mirror)/g' /etc/apt/sources.list \\
	&& apt-get update \\
	&& apt-get install --no-install-recommends --no-install-suggests -y build-essential \\
	&& pip install --index-url $(pip_index) uwsgi \\
    && ldd /usr/local/bin/uwsgi | awk '/=>/{print $$(NF-1)}' | while read n; do dpkg-query -S $$n; done | sed 's/^\([^:]\+\):.*$$/\\1/' | sort | uniq > /requirements.apt
FROM $(baseimage) as BASE
COPY --from=BUILDER /usr/local/bin/uwsgi /usr/local/bin/uwsgi
COPY --from=BUILDER /requirements.apt /requirements.apt
COPY --from=BUILDER /etc/apt/sources.list /etc/apt/sources.list
COPY requirements.txt /usr/etc/
RUN set -x \\
	&& apt update \\
    && apt --no-install-recommends --no-install-suggests -y install curl $$(cat /requirements.apt) \\
    && apt-get clean && rm -rf /var/lib/apt/lists/* \\
    && rm -f /requirements.apt \\
	&& pip3 install --index-url $(pip_index) -r /usr/etc/requirements.txt
WORKDIR /usr/src/
CMD ["uwsgi", "-y", "/usr/src/uwsgi/config.yaml"]
endef

export IMAGECMD

all :
	echo hola

################################################################################

init: export baseimage=$(image)
init:
ifneq ($(and $(M9_RUNTIME),$(M9_PROJECT)),)
	@mkdir -p $(runtime_path)
	@echo "$$IMAGECMD" > $(runtime_path)/Dockerfile
	@cp requirements.txt $(runtime_path)
	@$(cli) build $(runtime_path) -t $(M9_PROJECT).$(M9_RUNTIME)

  ifneq ($(shell grep 'M9_PLACEHOLDER_port' uwsgi/config.yaml),)
	@python -c "import socket; s=socket.socket(); s.bind(('', 0)); unp=s.getsockname()[1]; s.close(); \
    c=open('uwsgi/config.yaml');r=c.read().replace('M9_PLACEHOLDER_port', str(unp));c.close(); \
	c=open('uwsgi/config.yaml','w');c.write(r);c.close(); \
	print('default uwsgi port is:', unp);"
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

ifneq ($(and $(ENV_host_port),$(ENV_uwsgi_port)),)
net_mode = -p $(host_port):$(uwsgi_port)
else
net_mode = --network host
endif

localmount =
ifneq (,$(wildcard wsgi*))
localmount = -v ./:/usr/src/:Z
endif

env_file =
ifneq (,$(wildcard .env))
env_file = --env-file .env
endif

up:
ifdef M9_RUNTIME_FULLNAME
	$(cli)  run $(up_mode) $(daemon) $(net_mode) $(env_file) $(localmount) \
    -v ./uwsgi/:/usr/src/uwsgi/:Z \
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
	@$(cli) run --rm -v ./:/usr/src/:Z $(M9_PROJECT).$(M9_RUNTIME)_build python3 -m nuitka --module --include-module=wsgi wsgi

################################################################################

ifeq ($(M9_RUNTIME), default)
mkfile = Makefile
else
mkfile = Makefile.$(M9_RUNTIME)
endif

dist:
	@rm -rf ./dist && mkdir ./dist/

ifeq ($(M9_ARGS_distway), source)
	@cp -r wsgi/ ./dist/
endif
ifeq ($(M9_ARGS_distway), binary)
	@cp ./wsgi.*.so ./dist/
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
	@cp --parents uwsgi/config.yaml ./dist/
	@python -c "import json,datetime;c=open('./dist/.m9/meta.json'); r=json.load(c);c.close(); \
	r['project_dir']=None;r['dist_runtime']='$(M9_RUNTIME)';r['dist_way']='$(M9_ARGS_distway)';r['dist_image']='$(M9_ARGS_distimage)';r['dist_at']=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'); \
	c=open('./dist/.m9/meta.json','w');c.write(json.dumps(r));c.close()"

################################################################################

deploy:
ifndef M9_ARGS_distimage
	@$(cli) build $(runtime_path) -t $(M9_PROJECT).$(M9_RUNTIME)
	@cp -Trvf $(runtime_path) $(M9_ARGS_targetdir)/$(runtime_path) || :
  ifeq ($(M9_ARGS_distway), source)
	@cp -vfr ./wsgi $(M9_ARGS_targetdir) || :
  endif
  ifeq ($(M9_ARGS_distway), binary)
	@cp -vf ./wsgi.*.so $(M9_ARGS_targetdir) || :
  endif
else
	@([ -e $(M9_PROJECT).$(M9_RUNTIME).$(M9_ARGS_distimage).tar ] && $(cli) load -i $(M9_PROJECT).$(M9_RUNTIME).$(M9_ARGS_distimage).tar) || echo image file not found 
	@$(cli) tag $(M9_PROJECT).$(M9_RUNTIME)_distimage:$(M9_ARGS_distimage) $(M9_PROJECT).$(M9_RUNTIME):latest
endif
	@cp -vf .env $(M9_ARGS_targetdir) || :
	@cp -vf --parents .m9/$(mkfile) $(M9_ARGS_targetdir) || :
	@cp -vf --parents uwsgi/config.yaml $(M9_ARGS_targetdir) || :

################################################################################
