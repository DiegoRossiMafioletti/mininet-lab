Traffic Monitor with Sketches in Software Defined Networks using Ryu and Mininet
----

# About

This is part of tasks in my discipline `Advanced Computers Networks` on my master degree at UFES.

At this work, I'll define a simple network topology with a network monitor using sketches do detect probables deny of services (DoS) attack.

# Requirements

Docker! (and docker compose)

# Network topology

```
+--------+ +--------+ +--------+    +---------+  +---------+ +---------+
|        | |        | |        |    |         |  |         | |         |
|        | |        | |        |    |         |  |         | |         |
| h41    | | h42    | |  h43   |    |  h31    |  |   h32   | |  h33    |
|        | |        | |        |    |         |  |         | |         |
+---+----+ +----+---+ +--+-----+    +-----+---+  +----+----+ +----+----+
    |           |        |                |           |           |
    |           |        |                |           |           |
    |           |        |                |           |           |
    |           |  +-----+--+             |       +---+----+      |
    |           |  |        |             +-------+        |      |
    |           +--+        |                     |        +------+
    +--------------+   s04  +---------------------+   s03  |
                   |        |                     |        |
                   +--------+                     +----+---+
                                                       |
                                                       |
                                                       |
                    +------+                     +-----+--+
                    |      |                     |        |
           +--------+ s01  +---------------------+  s02   +------+
           |        |      +----+            +---+        |      |
           |        +-+----+    |            |   +----+---+      |
           |          |         |            |        |          |
           |          |         |            |        |          |
           |          |         |            |        |          |
       +---+---+  +---+---+ +---+---+    +---+---+ +--+----+ +---+---+
       |       |  |       | |       |    |       | |       | |       |
       | h11   |  |  h12  | | h13   |    |  h21  | |  h22  | |  h23  |
       |       |  |       | |       |    |       | |       | |       |
       +-------+  +-------+ +-------+    +-------+ +-------+ +-------+
```

* h11: 10.0.1.1
* h12: 10.0.1.2
* h13: 10.0.1.3
* h21: 10.0.2.1
* h22: 10.0.2.2
* h23: 10.0.2.3
* h31: 10.0.3.1
* h32: 10.0.3.2
* h33: 10.0.3.3
* h41: 10.0.4.1
* h42: 10.0.4.2
* h43: 10.0.4.3

# How to run

    # first terminal: compile syn flood script
    host> docker-compose exec mininet bash
    docker> cd syn_flooder
    docker> make clean all

    # second terminal: run ryu
    host> docker-compose up -d
    host> docker-compose exec mininet bash
    docker> ryu-manager src/monitor.py

    # third terminal: run topology
    host> docker-compose exec mininet bash
    docker> python src/topology.py
    mininet> pingall
    mininet> h42 python -m SimpleHTTPServer 80 >& /tmp/http.log &
    mininet> h42 wireshark &
    mininet> h23 ab -n 10000 -c 10 http://10.0.4.2


# Clean up environment

    host> docker-compose kill
    host> docker-compose rm

# How to check

Look terminal output.

# References

* [Mininet](http://mininet.org)
* [Ryu](https://osrg.github.io/ryu/)
* [Python](https://www.python.org/)
* [Docker](https://www.docker.com/)
