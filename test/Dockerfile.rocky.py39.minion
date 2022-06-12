FROM rockylinux:8.5

# install misc libs
RUN dnf install -y python3.9 nano tree openssh-server openssh-clients

# do python libs installation
RUN python3 -m pip install pip setuptools wheel --upgrade
RUN python3 -m pip install salt

# copy proxy-minion configuration across
COPY salt_nornir/test/proxy /etc/salt/proxy

# run Salt Nornir libs installation from local files
COPY salt_nornir/ /tmp/salt_nornir/
COPY nornir_salt/ /tmp/nornir_salt/
RUN python3 -m pip install /tmp/nornir_salt/.[prodmax] --upgrade
RUN python3 -m pip install /tmp/salt_nornir/.[prodmax] --upgrade

ENTRYPOINT salt-proxy --proxyid=$PROXY_ID -l debug