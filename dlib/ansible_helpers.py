import json
import ansible.inventory
import ansible.runner


def flatten_ansible_struct(struct, custom_output=None):
    """
    Make an ansible dictionary usable for mounting by moving the everything under the
    "contacted" key one level higher and inserting things like local facts.

    :param struct: A dictionary created with ansible.runner
    :type struct: dict
    :param custom_output: Dictionary containing the output of custom commands.
    :return: A modified (flattened and enriched) structure
    :rtype: dict
    """
    newstruct = {}
    tempstruct = {}
    try:
        for host in struct['contacted']:
            tempstruct[host] = struct['contacted'][host]['ansible_facts']
    except KeyError:
        pass

    # Remove ipv4 and put contents one "dir" higher
    for host in tempstruct.keys():
        for item in tempstruct[host].keys():
            try:
                newstruct[host][item] = tempstruct[host][item]
            except KeyError:
                newstruct[host] = {item: tempstruct[host][item]}

    # Rename ansible_local to local_facts if any
    for host in newstruct.keys():
        try:
            newstruct[host]['local_facts'] = newstruct[host].pop('ansible_local')
        except KeyError:
            pass

    # Walk through "ansible_mounts" (list) and create direntries
    for host in newstruct.keys():
        for mount in newstruct[host]['ansible_mounts']:
            diskname = mount['device'].split('/')[-1]
            try:
                newstruct[host]['mounts'][diskname] = mount
            except KeyError:
                newstruct[host]['mounts'] = {diskname: mount}

        newstruct[host].pop('ansible_mounts')

    if custom_output:
        # Remove empty dicts
        [custom_output.pop(i) for i in custom_output.keys() if custom_output[i] == {}]
        for filename in custom_output.keys():
            if not custom_output[filename]:
                continue

            for host in custom_output[filename]['contacted'].keys():
                if host not in newstruct.keys():
                    continue

                output = custom_output[filename]['contacted'][host]
                try:
                    newstruct[host]['custom_commands'][filename] = output
                except KeyError:
                    newstruct[host]['custom_commands'] = {filename: output}

    # Remove SSH_AUTH_SOCK from ansible_env
    for host in newstruct.keys():
        try:
            newstruct[host]['ansible_env'].pop('SSH_AUTH_SOCK')
        except KeyError:
            pass

    return newstruct


def get_real_data(host, custom_commands=None):
    """
    Runs the setup module on a host. When passed a custom command, it is appended to the returned struct

    :param host: The host to run on
    :type host: str
    :param custom_commands: The custom command that needs to be included
    :type custom_commands: list
    :return: A dictionary containing the output of the setup module as generated by ansible.runner.Runner
    :rtype: dict

    """
    runner = ansible.runner.Runner(
        module_name="setup",
        module_args="",
        forks=1,
        pattern=host,
    )
    data = runner.run()

    try:
        struct = flatten_ansible_struct(data)
        if custom_commands:
            struct[host]['custom_commands'] = custom_commands
        return struct
    except KeyError:
        pass


def run_custom_command(host, command, run_pattern=None, skeleton=False):
    """
    Runs a custom command on a host and returns the output in a dictionary as generated by ansible.runner.Runner

    :param host: Hostname of the server to run on
    :type host: string
    :param command: command to execute via the shell module from ansible
    :type command: string
    :param run_pattern: The pattern of hosts reachable via ansible
    :type run_pattern: list
    :param skeleton: Whether we are generating a skeleton. If True, don't actually run anything.
    :type skeleton: bool
    :return: Datastructure generated by ansible.runner.Runner
    :rtype: dict
    """

    if not run_pattern:
        run_pattern = []

    inventory = ansible.inventory.Inventory()
    run_host_inventory = [i.name for i in inventory.get_hosts(run_pattern)]
    custom_inventory = [i.name for i in inventory.get_hosts(host)]
    new_pattern = []

    for run_host in custom_inventory:
        if run_host in run_host_inventory:
            new_pattern.append(run_host)

    if not new_pattern:
        return None

    host = ':'.join(new_pattern)

    if skeleton:
        ret_dict = {}
        for h in new_pattern:
            try:
                ret_dict['contacted'][h] = {
                    'cmd': command,
                    'stdout': '',
                }
            except KeyError:
                ret_dict['contacted'] = {
                    h: {
                        'cmd': command,
                        'stdout': '',
                    }
                }
        return ret_dict

    runner = ansible.runner.Runner(
        module_name="shell",
        module_args=command,
        pattern=host,
    )
    return runner.run()


def gen_runner(pattern, forks=50, timeout=5):
    import ansible.runner
    """
    Create an ansible runner for the setup module

    :param pattern: Host pattern to run on
    :type pattern: str
    :param forks: Number of concurrent connections to use
    :type forks: int
    :param timeout: Seconds after which to timeout
    :type timeout: int
    :return: An instance of ansible.runner.Runner
    :rtype: ansible.runner.Runner
    """
    runner = ansible.runner.Runner(
        module_name="setup",
        module_args="",
        forks=forks,
        pattern=pattern,
        timeout=timeout,
    )

    return runner


def fetch_struct(pattern, retries=0):
    """
    Create a basic structure using ansible's Runner

    :param pattern: Host pattern to run on
    :type pattern: str
    :param retries: Number of retries to use when host is unreachable or times out
    :type retries: int
    :return: A dictionary containting the output of the setup module
    :rtype: dict
    """
    runner = gen_runner(pattern)
    struct = runner.run()

    for r in range(int(retries)):
        if not len(struct['dark']) == 0:
            newpattern = ':'.join(struct['dark'].keys())
            print "Retrying %s" % newpattern
            newrunner = gen_runner(newpattern, forks=10, timeout=2)
            newstruct = newrunner.run()
            for host in newstruct['contacted'].keys():
                try:
                    struct['dark'].pop(host)
                except KeyError:
                    pass
            for host in newstruct['contacted'].keys():
                struct['contacted'][host] = newstruct['contacted'][host]

    return struct


def gut_struct(struct):
    """
    Given a structure, recursively replace every string with an empty one

    :param struct: The structure to clean up
    :type struct: dict
    :return: The cleaned up dictionary/structure
    :rtye: dict
    """
    if type(struct) == dict:
        for k in struct.keys():
            if k == 'cmd':
                continue
            if type(struct[k]) == unicode or type(struct[k]) == int:
                struct[k] = ''
            if type(struct[k]) == list:
                struct.pop(k)
                continue
            gut_struct(struct[k])


def save_struct(jsonfile, struct):
    """
    Save the passed structure/dict to json

    :param jsonfile: Path to the file to write to
    :type jsonfile: str
    :param struct: structure to save
    :type struct: dict
    :rtype: None
    """
    f = open(jsonfile, 'wb')
    json.dump(struct, f)
    f.close()
