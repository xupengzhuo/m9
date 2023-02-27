# template: redissvc

runtime_path = .m9/runtime/$(M9_RUNTIME)

.PHONY : all init up down log dist deploy

cli = podman
image = redis:alpine

define IMAGECMD
FROM $(baseimage)
endef

export IMAGECMD

################################################################################

init: export baseimage=$(image)
init:
ifneq ($(and $(M9_RUNTIME),$(M9_PROJECT)),)
	@mkdir -p $(runtime_path)
	@mkdir -p /var/lib/redis/$(M9_PROJECT).$(M9_RUNTIME) && chmod a+w /var/lib/redis/$(M9_PROJECT).$(M9_RUNTIME)
	@echo "$$IMAGECMD" > $(runtime_path)/Dockerfile
	@$(cli) build $(runtime_path) -t $(M9_PROJECT).$(M9_RUNTIME)
	
  ifneq ($(shell grep 'M9_PLACEHOLDER_port' redis.conf),)
	@python -c "import socket; s=socket.socket(); s.bind(('', 0)); unp=s.getsockname()[1]; s.close(); \
    c=open('redis.conf');r=c.read().replace('M9_PLACEHOLDER_port', str(unp));c.close(); \
	c=open('redis.conf','w');c.write(r);c.close(); \
	print('default redis port is:', unp);"
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

ifneq ($(and $(ENV_host_port),$(ENV_redis_port)),)
net_mode = -p $(host_port):$(redis_port)
else
net_mode = --network host
endif

up:
ifdef M9_RUNTIME_FULLNAME
	$(cli) run $(up_mode) $(daemon) $(net_mode) \
	-v ./redis.conf:/usr/local/etc/redis/redis.conf \
	-v /var/lib/redis/$(M9_RUNTIME_FULLNAME):/data \
	-v /etc/localtime:/etc/localtime \
	--name=$(M9_RUNTIME_FULLNAME) $(M9_RUNTIME_FULLNAME) redis-server /usr/local/etc/redis/redis.conf
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

ifeq ($(M9_RUNTIME), default)
mkfile = Makefile
else
mkfile = Makefile.$(M9_RUNTIME)
endif

dist:
	@rm -rf ./dist && mkdir ./dist/
	@cp --parents .m9/meta.json .m9/$(mkfile) ./dist/
	@cp -r --parents .m9/runtime/$(M9_RUNTIME) ./dist/
	@cp --parents redis.conf ./dist/
	@python -c "import json,datetime;c=open('./dist/.m9/meta.json'); r=json.load(c);c.close(); \
	r['project_dir']=None;r['dist_runtime']='$(M9_RUNTIME)';r['dist_way']='$(M9_ARGS_distway)';r['dist_image']='$(M9_ARGS_distimage)';r['dist_at']=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'); \
	c=open('./dist/.m9/meta.json','w');c.write(json.dumps(r));c.close()"

################################################################################

deploy:
ifndef M9_ARGS_distimage
	@$(cli) build $(runtime_path) -t $(M9_PROJECT).$(M9_RUNTIME)
else
	@([ -e $(M9_PROJECT).$(M9_RUNTIME).$(M9_ARGS_distimage).tar ] && $(cli) load -i $(M9_PROJECT).$(M9_RUNTIME).$(M9_ARGS_distimage).tar) || echo image file not found 
	@$(cli) tag $(M9_PROJECT).$(M9_RUNTIME)_distimage:$(M9_ARGS_distimage) $(M9_PROJECT).$(M9_RUNTIME):latest
endif
	@cp -Trvf $(runtime_path) $(M9_ARGS_targetdir)/$(runtime_path) || :
	@cp -vf --parents .m9/$(mkfile) $(M9_ARGS_targetdir) || :
	@cp -vf redis.conf $(M9_ARGS_targetdir) || :
	@mkdir -p /var/lib/redis/$(M9_PROJECT).$(M9_RUNTIME) && chmod a+w /var/lib/redis/$(M9_PROJECT).$(M9_RUNTIME)
