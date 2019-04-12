Para carregar uma topologia no mininet:

Topologia simples, carregando através do mininet (topo-2sw-2host.py):
```bash
$ sudo mn –-custom=topo-2sw-2host.py --topo mytopo --test pingall
```

Topologia autônoma simples, via linha de comando (mytopo.py):
```bash
$ chmod +x mytopo.py
$ sudo ./mytopo.py
```