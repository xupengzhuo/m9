runtime_path = .m9/runtime/$(M9_RUNTIME)

.PHONY : all init up down log

all :
	echo hola

################################################################################
unsed_port := $(shell python -c 'import socket; s=socket.socket(); s.bind(("", 0)); print(s.getsockname()[1])')

init:
ifneq ($(and $(M9_RUNTIME),$(M9_BASEIMAGE),$(M9_PROJECT)),)
	@mkdir -p $(runtime_path); 
	@cp  ${M9_BASEIMAGE}/* $(runtime_path);
	@podman build $(runtime_path) -t $(M9_PROJECT).$(M9_RUNTIME);

	@python -c "c=open('redis.conf'); \
	r=c.read().replace('M9_PLACEHOLDER_port','${unsed_port}');c.close(); \
	c=open('redis.conf','w');c.write(r);c.close()";
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

ifneq ($(and $(ENV_host_port),$(ENV_redis_port)),)
net_mode = -p $(host_port):$(redis_port)
else
net_mode = --network host
endif

up:
ifdef M9_RUNTIME_FULLNAME
	podman run $(up_mode) $(daemon) $(net_mode) --env-file .env \
	-v ./:/usr/src/:Z \
	-v /etc/localtime:/etc/localtime \
	--name=$(M9_RUNTIME_FULLNAME) $(M9_RUNTIME_FULLNAME) redis-server ./redis.conf;
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
