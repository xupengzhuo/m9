# m9
### Installation

```git clone https://github.com/xupengzhuo/m9.git <YOUR PATH> ```

```chmod +x <YOUR PATH>/main.py && ln -s <YOUR PATH>/main.py /usr/local/bin/m9 ```


### Quick Start

- create a m9 project # unitpyapi is a template\
```m9 new unitpyapi testm9proj```

- create a runtime for testm9proj\
```m9 init helloapi -p ./testm9proj/```


- startup a project runtime\
```m9 up testm9proj.helloapi```

- compile project source code\
```m9 build testm9proj.helloapi```

- distribute project runtime with source code\
```m9 dist -s testm9proj.helloapi```

- distribute project runtime with binary\
```m9 dist -b testm9proj.helloapi```

- deploy project runtime in another system\
```m9 deploy <DISTRIBUTION FOLDER>```

- print all m9 objects\
```m9 list```

#### systemd command sets
m9 sd install|uninstall|enable|disable|start|stop|status <runtime>   # you can use "all" as runtime

- generate systemd unit files for m9 runtime and install them\
```m9 sd install <runtime>```
- stop runtime and remove systemd unit files\
```m9 sd uninstall <runtime>```
- same as systemctl enable\
```m9 sd enable <runtime>```
- same as systemctl disable\
```m9 sd disable <runtime>```
- same as start start\
```m9 sd enable <runtime>```
- same as systemctl stop\
```m9 sd stop <runtime>```

- print systemd unit status (systemctl subcommand `is-active` and `is-enabled`) \
```m9 sd status <runtime>```
