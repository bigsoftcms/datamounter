FuseMounter
=======

FUSE filesystem populated using the setup module from [Ansible].

Usage
-----
```
ansfuse.py [-h] [--gen-cache GENCACHE] [--cache CACHE]
                  [--pattern PATTERN] [--mountpoint MOUNTPOINT]

optional arguments:
  -h, --help            show this help message and exit
  --gen-cache GENCACHE, -g GENCACHE
                        Write a cache file at this location.
  --cache CACHE, -c CACHE
                        Location of the cache-file if wanted
  --pattern PATTERN, -p PATTERN
                        Pattern to extract info from. Needed when generating a
                        cache file and when not using a cache file
  --foreground, -f      Run in foreground
  --retries RETRIES, -r RETRIES
                        Optional number of retries to contact unreachable
                        hosts
  --custom CUSTOM       Optional ini file with custom commands to run on
                        remote host which output to expose
```

Example Usage
-----
Map the pre-generated datafile stored in **dev.pkl** on **/opt/infra_map**:

```ansfuse.py -c dev.pkl -m /opt/infra_map```

Scan the **production-env** (as defined in your [ansible inventory]), save it in **prod.pkl** and map in on **/opt/infra/prod**:

```ansfuse.py -g prod.pkl -p production-env -m /opt/infra_prod```

[Ansible]:http://www.ansible.com/
[ansible inventory]:http://docs.ansible.com/intro_inventory.html
