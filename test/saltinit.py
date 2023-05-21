#!/usr/bin/env python3
import asyncio
import json
import os
import signal


async def main():
    futures = []
    futures.append(await asyncio.create_subprocess_exec("salt-master", '-l', 'debug'))
    futures.append(await asyncio.create_subprocess_exec("salt-proxy", '--proxyid=nrp1', '--log-level=debug', '--log-file=/var/log/salt/proxy-nrp1'))
    futures.append(await asyncio.create_subprocess_exec("salt-proxy", '--proxyid=nrp2', '--log-level=debug', '--log-file=/var/log/salt/proxy-nrp2'))
    futures.append(await asyncio.create_subprocess_exec("salt-proxy", '--proxyid=nrp3', '--log-level=debug', '--log-file=/var/log/salt/proxy-nrp3'))
    await asyncio.gather(*[future.communicate() for future in futures])

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    for signame in {"SIGINT", "SIGTERM"}:
        loop.add_signal_handler(getattr(signal, signame), loop.stop)
    try:
        loop.run_until_complete(main())
    finally:
        loop.close()
