FROM osrg/ryu-book

ENV APT_PKGS="\
    build-essential vim tmux htop wget netcat \
    nmap iptables wireshark firefox apache2-utils" \
    PIP_PKGS="\
    pyprobables flask"

RUN apt update; \
    apt dist-upgrade -y; \
    DEBIAN_FRONTEND=noninteractive apt install -y ${APT_PKGS}; \
    pip install -U ${PIP_PKGS}; \
    wget https://raw.githubusercontent.com/jvrmaia/dotfiles/master/.tmux.conf.without_gui -O /root/.tmux.conf;

WORKDIR /opt

ADD . /opt
