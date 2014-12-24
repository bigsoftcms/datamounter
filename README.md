Datamounter
=======

FUSE filesystem populated from JSON. Optionally from ansible's setup module

Components
-----
ansible_fetcher.py can be used to fetch information using Ansible's setup module
and optionally custom commands/facts. It outputs a slightly modified json file for
use with the datamounter.py script.

Usage ansible_fetcher.py
-----
```
usage: ansible_fetcher.py [-h] [--pattern PATTERN] [--retries RETRIES] -f
                          FILENAME [--custom CUSTOM] [--skeleton]

Fetch information from remote systems using Ansible

optional arguments:
  -h, --help            show this help message and exit
  --pattern PATTERN, -p PATTERN
                        Pattern to extract info from. Needed when generating a
                        cache file and when not using a cache file
  --retries RETRIES, -r RETRIES
                        Optional number of retries to contact unreachable
                        hosts
  -f FILENAME, --filename FILENAME
                        Destination filename for the json data.
  --custom CUSTOM       Optional ini file with custom commands to run on
                        remote host which output to expose. Files will show up
                        under custom_facts/.
  --skeleton, -s        Remove all values from the datastructure, essentially
                        leaving only the structure itself. Useful in
                        combination with --realtime
```

Usage datamounter.py
-----
```
usage: ansible_fetcher.py [-h] [--pattern PATTERN] [--retries RETRIES] -f
                          FILENAME [--custom CUSTOM] [--skeleton]

Fetch information from remote systems using Ansible

optional arguments:
  -h, --help            show this help message and exit
  --pattern PATTERN, -p PATTERN
                        Pattern to extract info from. Needed when generating a
                        cache file and when not using a cache file
  --retries RETRIES, -r RETRIES
                        Optional number of retries to contact unreachable
                        hosts
  -f FILENAME, --filename FILENAME
                        Destination filename for the json data.
  --custom CUSTOM       Optional ini file with custom commands to run on
                        remote host which output to expose. Files will show up
                        under custom_facts/.
  --skeleton, -s        Remove all values from the datastructure, essentially
                        leaving only the structure itself. Useful in
                        combination with --realtime
```

Example Usage
-----
Map the pre-generated datafile stored in **dev.json** on **/opt/infra_map**:

```datamounter.py -c dev.json /opt/infra_map```


Create a json file for all the **prod** hosts as defined in [ansible inventory] and save it to **prod.json**:

```ansible_fetcher.py -p prod -f prod.json```

Mount a generated json file named **prod.json** on /opt/infra_prod:

```datamounter.py -c prod.json /opt/infra_prod```

The resulting mount will contain a directory for each host and within that directory all the gathered facts. Note that the mounts are put in $host/mounts and that local facts (as put in /etc/ansible/facts.d) are put in $host/local_facts.

It is also possible to map the output of arbitrary commands using the --custom parameter. These files will be put in $host/custom_commands

[Ansible]:http://www.ansible.com/
[ansible inventory]:http://docs.ansible.com/intro_inventory.html
