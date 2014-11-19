import ansible.runner

def flatten_ansible_struct(struct, custom_output=None):
    newstruct = {}
    tempstruct = {}
    for host in struct['contacted']:
        tempstruct[host] = struct['contacted'][host]['ansible_facts']

    # Remove ipv4 and put contents one "dir" higher
    for host in tempstruct.keys():
        for item in tempstruct[host].keys():
            try:
                newstruct[host][item] = tempstruct[host][item]
            except KeyError:
                newstruct[host] = {item: tempstruct[host][item]}

    # Rename ansible_local to local_facts if any
    try:
        for host in newstruct.keys():
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
        for filename in custom_output.keys():
            for host in custom_output[filename]['contacted'].keys():
                output = custom_output[filename]['contacted'][host]['stdout']
                newstruct[host]['custom_commands'] = {filename: output}

    return newstruct

def get_real_data(host):
    runner = ansible.runner.Runner(
            module_name="setup",
            module_args="",
            forks=1,
            pattern=host,
    )
    data = runner.run()

    try:
        return flatten_ansible_struct(data)
    except KeyError:
        pass

def run_custom_command(pattern, command):
    runner = ansible.runner.Runner(
            module_name="shell",
            module_args=command,
            pattern=pattern,
    )
    return runner.run()

def gen_runner(pattern):
    runner = ansible.runner.Runner(
            module_name="setup",
            module_args="",
            forks=10,
            pattern=pattern,
    )

    return runner

def fetch_struct(pattern, retries=0):
    runner = gen_runner(pattern)
    struct = runner.run()

    for r in range(int(retries)):
        if not len(struct['dark']) == 0:
            newpattern = ':'.join(struct['dark'].keys())
            print "Retrying %s" % newpattern
            newrunner = gen_runner(newpattern)
            newstruct = newrunner.run()
            for host in newstruct['contacted'].keys():
                try:
                    struct['dark'].pop(host)
                except KeyError:
                    pass
            for host in newstruct['contacted'].keys():
                struct['contacted'][host] = newstruct['contacted'][host]

    return struct
