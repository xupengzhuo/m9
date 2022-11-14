# m9
### Installation

```git pull https://github.com/xupengzhuo/m9.git <YOUR PATH> ```

```chmod +x <YOUR PATH>/main.py && ln -s <YOUR PATH>/main.py /usr/local/bin/m9 ```


### Quick Start


- create a m9 project # unitpyapi is a template
```m9 new unitpyapi testm9proj```

- create a runtime for testm9proj
```m9 init helloapi -p ./testm9proj/```


- startup a project runtime
```m9 up testm9proj.helloapi```

- compile project source code
```m9 build testm9proj.helloapi```

- print all m9 objects
```m9 list```
