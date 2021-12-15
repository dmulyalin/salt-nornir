FROM ceosimage:4.26.0F

ENV INTFTYPE=eth 
ENV ETBA=1 
ENV SKIP_ZEROTOUCH_BARRIER_IN_SYSDBINIT=1 
ENV CEOS=1 
ENV EOS_PLATFORM=ceoslab 
ENV container=docker
ENV MGMT_INTF=eth21

COPY salt_nornir/test/ceos2.cfg /mnt/flash/startup-config

CMD ["/sbin/init", "systemd.setenv=INTFTYPE=eth", "systemd.setenv=ETBA=1", "systemd.setenv=SKIP_ZEROTOUCH_BARRIER_IN_SYSDBINIT=1", "systemd.setenv=CEOS=1", " systemd.setenv=EOS_PLATFORM=ceoslab", "systemd.setenv=container=docker"]