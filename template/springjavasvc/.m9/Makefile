runtime_path = .m9/runtime/$(M9_RUNTIME)

.PHONY : all init up down log re build dist deploy

cli = podman
image = maven:3.8.6-jdk-8-slim
image_build = maven:3.8.6-jdk-8-slim

define IMAGECMD
FROM $(baseimage) as BUILDER
WORKDIR /usr/src/
COPY src /usr/src
COPY settings.xml /usr/share/maven/conf
RUN set -ex \\
	&& mvn -B -f pom.xml clean source:jar install package -Dmaven.test.skip=true -P test -DconfEnv=test dependency:tree
FROM $(baseimage) as BASE
COPY entrypoint.sh /usr/local/bin/
COPY --from=BUILDER /usr/src/target/application.jar /usr/src/app.jar 
RUN chmod +x /usr/local/bin/entrypoint.sh
WORKDIR /usr/src/
STOPSIGNAL SIGTERM
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
endef

define ENTRYPOINT
#!/bin/sh
set -e
exec java $$JAVAOPTS \
-XX:G1HeapRegionSize=8m \
-XX:MaxTenuringThreshold=10 \
-XX:+UseG1GC \
-XX:InitiatingHeapOccupancyPercent=45 \
-XX:MaxGCPauseMillis=200 -XX:+PrintGCDateStamps \
-XX:+PrintGCDetails -Dspring.profiles.active=$$PROFILE -Dserver.port=$$PORT \
-verbose:gc -Xloggc:/tmp/gc.log \
-jar app.jar
endef

export ENTRYPOINT
export IMAGECMD

################################################################################

init: export baseimage=$(image)
init:
	@mkdir -p $(runtime_path); 
	@echo "$$ENTRYPOINT" > $(runtime_path)/entrypoint.sh
	@echo "$$IMAGECMD" > $(runtime_path)/Dockerfile
	@cp -r settings.xml src/ $(runtime_path)
	@$(cli) build $(runtime_path) -t $(M9_PROJECT).$(M9_RUNTIME)

  ifneq ($(shell grep 'M9_PLACEHOLDER_port' .env),)
	@python -c "import socket; s=socket.socket(); s.bind(('', 0)); unp=s.getsockname()[1]; s.close(); \
    c=open('.env');r=c.read().replace('M9_PLACEHOLDER_port', str(unp));c.close(); \
	c=open('.env','w');c.write(r);c.close(); \
	print('default spring port is:', unp);"
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

ifneq ($(and $(ENV_host_port),$(ENV_spring_port)),)
net_mode = -p $(host_port):$(ENV_spring_port)
else
net_mode = --network host
endif

localmount =
ifneq (,$(wildcard *.jar))
localmount = -v ./:/usr/src/:Z
endif

env_file =
ifneq (,$(wildcard .env))
env_file = --env-file .env
endif

up:
ifdef M9_RUNTIME_FULLNAME
	$(cli)  run $(up_mode) $(daemon) $(net_mode) $(env_file) $(localmount) \
    -v ./config/:/usr/src/config/:Z \
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
	@mkdir -p $(runtime_path); 
	@echo "$$ENTRYPOINT" > $(runtime_path)/entrypoint.sh
	@echo "$$IMAGECMD" > $(runtime_path)/Dockerfile
	@cp -r settings.xml src/ $(runtime_path)
	@$(cli) build $(runtime_path) -t $(M9_PROJECT).$(M9_RUNTIME)
	@mkdir -p ./build/ 
	@$(cli) run --rm --entrypoint cp -v ./build/:/tmp/:Z $(M9_PROJECT).$(M9_RUNTIME) /usr/src/app.jar /tmp/

################################################################################

ifeq ($(M9_RUNTIME), default)
mkfile = Makefile
else
mkfile = Makefile.$(M9_RUNTIME)
endif

dist:
ifeq ($(M9_ARGS_distway), source)
	@echo This type of project does not support distribution via source code
	exit 1
endif
	@rm -rf ./dist && mkdir ./dist/
ifeq ($(M9_ARGS_distway), binary)
	@cp ./build/*.jar ./dist/
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
	@cp --parents .m9/meta.json .m9/$(mkfile) .m9/project.json ./dist/
	@cp -r --parents .m9/runtime/$(M9_RUNTIME) ./dist/
	@cp -r ./config/ ./dist/
	@python -c "import json,datetime;c=open('./dist/.m9/meta.json'); r=json.load(c);c.close(); \
	r['project_dir']=None;r['dist_runtime']='$(M9_RUNTIME)';r['dist_way']='$(M9_ARGS_distway)';r['dist_image']='$(M9_ARGS_distimage)';r['dist_at']=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'); \
	c=open('./dist/.m9/meta.json','w');c.write(json.dumps(r));c.close()"

################################################################################

deploy:
ifndef M9_ARGS_distimage
	@$(cli) build $(runtime_path) -t $(M9_PROJECT).$(M9_RUNTIME)
	@cp -Trvf $(runtime_path) $(M9_ARGS_targetdir)/$(runtime_path) || :
  ifeq ($(M9_ARGS_distway), binary)
	@cp -vf ./*.jar $(M9_ARGS_targetdir) || :
  endif
else
	@([ -e $(M9_PROJECT).$(M9_RUNTIME).$(M9_ARGS_distimage).tar ] && $(cli) load -i $(M9_PROJECT).$(M9_RUNTIME).$(M9_ARGS_distimage).tar) || echo image file not found 
	@$(cli) tag $(M9_PROJECT).$(M9_RUNTIME)_distimage:$(M9_ARGS_distimage) $(M9_PROJECT).$(M9_RUNTIME):latest
endif
	@cp -vf .env $(M9_ARGS_targetdir) || :
	@cp -vf --parents .m9/$(mkfile) .m9/project.json $(M9_ARGS_targetdir) || :
	@cp -vfr --parents config/ $(M9_ARGS_targetdir) || :

################################################################################
