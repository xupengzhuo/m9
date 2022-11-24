runtime_path = .m9/runtime/$(M9_RUNTIME)

.PHONY : all init up down log re build dist deploy

all :
	echo hola

################################################################################
define ENTRYPOINT
#!/bin/bash\nset -e\nif [ -e ./start.bin ]; then\n  exec ./start.bin\nelif [ -e ./start.py ]; then\n  exec python start.py\nfi\nexec "$@"
endef

export ENTRYPOINT
init:
ifneq ($(and $(M9_RUNTIME),$(M9_BASEIMAGE),$(M9_PROJECT)),)
	@mkdir -p $(runtime_path); 
	@cp  ${M9_BASEIMAGE}/* $(runtime_path);
	@echo -e $$ENTRYPOINT > $(runtime_path)/entrypoint.sh && chmod +x $(runtime_path)/entrypoint.sh;
	@cp ./requirements.txt $(runtime_path)/requirements.txt;
	@echo "COPY ./requirements.txt /usr/etc/" >> $(runtime_path)/Dockerfile;
	@echo "COPY ./entrypoint.sh /" >> $(runtime_path)/Dockerfile;
	@echo "RUN pip3 install -r /usr/etc/requirements.txt" >> $(runtime_path)/Dockerfile;
	@echo "ENTRYPOINT [\"/entrypoint.sh\"]" >> $(runtime_path)/Dockerfile;

	@podman build $(runtime_path) -t $(M9_PROJECT).$(M9_RUNTIME);

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

ifneq ($(and $(ENV_host_port),$(ENV_py_port)),)
net_mode = -p $(host_port):$(py_port)
else
net_mode = --network host
endif

up:
ifdef M9_RUNTIME_FULLNAME
	podman run $(up_mode) $(daemon) $(net_mode) --env-file .env \
	-v ./:/usr/src/:Z \
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
	@echo -e "\nnuitka\nordered-set" >> ./build/$(M9_RUNTIME)/requirements.txt;
	@podman build ./build/$(M9_RUNTIME) -t $(M9_PROJECT).$(M9_RUNTIME)_build ;
	@podman run --rm --entrypoint python3 -v ./:/usr/src/:Z $(M9_PROJECT).$(M9_RUNTIME)_build -m nuitka --follow-imports start.py;
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
	@cp -f start.py ./dist/;
endif
ifeq ($(M9_ARGS_distway), binary)
	@cp start.bin ./dist/;
endif
	@cp .env.dist ./dist/.env || (echo "[info] using '.env' for distribution if '.env.dist' not found" && cp .env ./dist/.env) ;
################################################################################

################################################################################
deploy:
	@podman build $(runtime_path) -t $(M9_PROJECT).$(M9_RUNTIME);
ifdef M9_ARGS_targetdir
	@[ -e ./start.py ] && cp -vf ./start.py $(M9_ARGS_targetdir)||:;
	@[ -e ./start.bin ] && cp -vf ./start.bin $(M9_ARGS_targetdir)||:;
	@cp -vf .env $(M9_ARGS_targetdir);
	@cp -vf --parents .m9/Makefile .m9/project.json $(M9_ARGS_targetdir);
	@cp -Trvf $(runtime_path) $(M9_ARGS_targetdir)/$(runtime_path);
endif
################################################################################
