runtime_path = .m9/runtime/$(M9_RUNTIME)

.PHONY : all init up down log re build dist deploy

all :
	echo hola

################################################################################
init:
	@mkdir -p $(runtime_path); 
	@echo  $(runtime_path), $(M9_RUNTIME), $(M9_BASEIMAGE), $(M9_PROJECT);
################################################################################

################################################################################
ifdef M9_ARGS_daemon
daemon =
else
daemon =
endif

ifdef M9_ARGS_dryrun
up_mode =
else
up_mode =  
endif

up:
ifdef M9_RUNTIME_FULLNAME
	@echo  $(runtime_path), $(M9_RUNTIME_FULLNAME), $(M9_ARGS_dryrun), $(M9_ARGS_daemon)
endif
################################################################################

################################################################################
ifdef M9_ARGS_follow
log_mode =
else
log_mode = 
endif

log:
ifdef M9_RUNTIME_FULLNAME
	@echo $(runtime_path), $(M9_RUNTIME_FULLNAME) 
endif
################################################################################

################################################################################
down:
ifdef M9_RUNTIME_FULLNAME
	@echo $(runtime_path), $(M9_RUNTIME_FULLNAME) 
endif
################################################################################

################################################################################
re:
ifdef M9_RUNTIME_FULLNAME
	@echo $(runtime_path), $(M9_RUNTIME_FULLNAME) 
endif
################################################################################

################################################################################
build:
	@echo $(runtime_path), $(M9_PROJECT), $(M9_RUNTIME), $(runtime_path) 
################################################################################

################################################################################
dist:
	@echo $(runtime_path), $(M9_RUNTIME), $(M9_ARGS_distway)

################################################################################

################################################################################
deploy:
	@echo $(runtime_path), $(M9_PROJECT), $(M9_RUNTIME), $(M9_ARGS_targetdir)
################################################################################
