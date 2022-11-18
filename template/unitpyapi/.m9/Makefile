runtime_path = .m9/runtime/$(M9_RUNTIME)

.PHONY : all init up down log re build dist deploy

all :
	echo hola

################################################################################
unsed_port := $(shell python -c 'import socket; s=socket.socket(); s.bind(("", 0)); print(s.getsockname()[1])')
init:
ifneq ($(and $(M9_RUNTIME),$(M9_BASEIMAGE),$(M9_PROJECT)),)
	@mkdir -p $(runtime_path); 
	@cp  ${M9_BASEIMAGE}/* $(runtime_path);
	@cp ./requirements.txt $(runtime_path)/requirements.txt;
	@echo "COPY ./requirements.txt /usr/etc/" >> $(runtime_path)/Dockerfile;
	@echo "RUN pip3 install -r /usr/etc/requirements.txt" >> $(runtime_path)/Dockerfile;

	@podman build $(runtime_path) -t $(M9_PROJECT).$(M9_RUNTIME);

	@python -c "c=open('unit/config.json'); \
	r=c.read().replace('M9_PLACEHOLDER_port','${unsed_port}');c.close(); \
	c=open('unit/config.json','w');c.write(r);c.close()";
	@echo default unit port is: $(unsed_port)
endif
################################################################################

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

up:
ifdef M9_RUNTIME_FULLNAME
	@mkdir -p ./unit/;
	podman run $(up_mode) $(daemon) $(net_mode) --env-file .env \
	-v ./:/usr/src/:Z \
	-v ./unit/:/var/run/:Z \
	-v ./unit/:/docker-entrypoint.d/:Z \
	-v /etc/localtime:/etc/localtime \
	--name=$(M9_RUNTIME_FULLNAME) $(M9_RUNTIME_FULLNAME);
endif
################################################################################

################################################################################
ifdef M9_ARGS_follow
log_mode = -f
else
log_mode = 
endif

log:
ifdef M9_RUNTIME_FULLNAME
	podman logs $(log_mode) $(M9_RUNTIME_FULLNAME) 
endif
################################################################################

################################################################################
down:
ifdef M9_RUNTIME_FULLNAME
	podman rm -f $(M9_RUNTIME_FULLNAME) 
endif
################################################################################

################################################################################
re:
ifdef M9_RUNTIME_FULLNAME
	podman restart $(M9_RUNTIME_FULLNAME)
endif
################################################################################

################################################################################
build:
	@mkdir -p ./build/;
	@cp -r $(runtime_path) ./build/;
	@echo -e "\nnuitka" >> ./build/$(M9_RUNTIME)/requirements.txt;
	@podman build ./build/$(M9_RUNTIME) -t $(M9_PROJECT).$(M9_RUNTIME)_build ;
	@podman run -v ./:/usr/src/:Z $(M9_PROJECT).$(M9_RUNTIME)_build python3 -m nuitka --module --include-module=asgi asgi;

################################################################################

################################################################################
dist:
	@rm -rf ./dist && mkdir ./dist/;
	@cp --parents .m9/meta.json .m9/Makefile .m9/project.json ./dist/;
	@python -c "import json;c=open('./dist/.m9/meta.json'); \
	r=json.load(c);c.close(); r['project_dir']=None;\
	c=open('./dist/.m9/meta.json','w');c.write(json.dumps(r));c.close()";
	@cp -r --parents .m9/runtime/$(M9_RUNTIME) ./dist/;
ifeq ($(M9_ARGS_distway), source)
	@cp -r ./asgi/ ./dist/;
endif
ifeq ($(M9_ARGS_distway), binary)
	@cp ./asgi.*.so ./dist/;
endif
	@cp --parents unit/config.json ./dist/;
	@cp .env.dist ./dist/.env || (echo "[info] using '.env' fot distribution if '.env.dist' not found" && cp .env ./dist/.env) ;

################################################################################

################################################################################
deploy:
	echo $(M9_ARGS_targetdir)
	@podman build $(runtime_path) -t $(M9_PROJECT).$(M9_RUNTIME);
	@cp -rf ./* $(M9_ARGS_targetdir);
################################################################################
