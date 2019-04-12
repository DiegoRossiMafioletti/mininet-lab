Para executar o controlador:

Em um terminal, execute o ryu-manager:
```bash
$ sudo ryu-manager <app.py>
```

Em outro terminal, execute o mininet:
```bash
$ sudo mn --topo=single,5 --controller=remote --mac
```
