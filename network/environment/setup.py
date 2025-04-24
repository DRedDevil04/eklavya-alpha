import os
import time
import libvirt
import paramiko
import sys
import xml.etree.ElementTree as ET
from time import sleep

class Environment:
    def __init__(self, base_image, ssh_user, ssh_password, scripts_dir, rebuild=False):
        self.base_image = os.path.expanduser(base_image)
        self.ssh_user = ssh_user
        self.ssh_password = ssh_password
        self.scripts_dir = scripts_dir
        self.rebuild = rebuild
        self.conn = None
        self.nodes = {
            "node1-linux": {
                "image": f"/home/nitu/Programs/projectSem6/eklavya-alpha/virt-images/node1.qcow2", 
                "script": f"{self.scripts_dir}/1.sh",
                "mac": "52:54:00:a1:b1:c1",
                "ip": None,
                "gui": False
            },
            "node2-linux": {
                "image": f"/home/nitu/Programs/projectSem6/eklavya-alpha/virt-images/node2.qcow2", 
                "script": f"{self.scripts_dir}/2.sh",
                "mac": "52:54:00:a2:b2:c2",
                "ip": None,
                "gui": False
            },
            "node3-linux": {
                "image": f"/home/nitu/Programs/projectSem6/eklavya-alpha/virt-images/node3.qcow2", 
                "script": f"{self.scripts_dir}/3.sh",
                "mac": "52:54:00:a3:b3:c3",
                "ip": None,
                "gui": False
            },
        }
        self.vm_template = """
        <domain type='kvm'>
          <name>{name}</name>
          <memory unit='MiB'>2048</memory>
          <vcpu placement='static'>2</vcpu>
          <os>
            <type arch='x86_64'>hvm</type>
            <boot dev='hd'/>
          </os>
          <features>
            <acpi/>
            <apic/>
          </features>
          <devices>
            <disk type='file' device='disk'>
              <driver name='qemu' type='qcow2'/>
              <source file='{image}'/>
              <target dev='vda' bus='virtio'/>
            </disk>
            <interface type='network'>
              <source network='default'/>
              <mac address='{mac}'/>
              <model type='virtio'/>
            </interface>
            <graphics type='vnc' port='-1' autoport='yes'/>
            <video>
              <model type='qxl'/>
            </video>
            <input type='tablet' bus='usb'/>
          </devices>
        </domain>
        """

    def connect_libvirt(self):
        if self.conn is None:
            self.conn = libvirt.open("qemu:///system")
            if self.conn is None:
                raise RuntimeError("Failed to connect to libvirt")

    def close_libvirt(self):
        if self.conn is not None:
            self.conn.close()
            self.conn = None

    def create_clones(self):
        for node, details in self.nodes.items():
            if os.path.exists(details["image"]):
                print(f"Image {details['image']} already exists, skipping clone.")
                continue
            print(f"Creating clone {details['image']}...")
            cmd = f"qemu-img create -f qcow2 -b {self.base_image} -F qcow2 {details['image']}"
            if os.system(cmd) != 0:
                raise RuntimeError(f"Failed to create clone {details['image']}")

    def check_vm_exists(self, name):
        try:
            return self.conn.lookupByName(name) is not None
        except libvirt.libvirtError:
            return False

    def create_vms(self):
        self.connect_libvirt()
        try:
            for node, details in self.nodes.items():
                if self.check_vm_exists(node):
                    print(f"VM {node} already exists, skipping creation.")
                    continue
                xml_config = self.vm_template.format(
                    name=node,
                    image=details["image"],
                    mac=details["mac"]
                )
                print(f"Creating {node}...")
                domain = self.conn.defineXML(xml_config)
                if domain is None:
                    raise RuntimeError(f"Failed to define VM {node}")
                if domain.create() < 0:
                    raise RuntimeError(f"Failed to start VM {node}")
                print(f"VM {node} started successfully")
        except libvirt.libvirtError as e:
            raise RuntimeError(f"Libvirt error: {e}")

    def get_vm_ip(self, domain_name, max_retries=30, wait_seconds=5):
        self.connect_libvirt()
        for _ in range(max_retries):
            try:
                domain = self.conn.lookupByName(domain_name)
                ifaces = domain.interfaceAddresses(libvirt.VIR_DOMAIN_INTERFACE_ADDRESSES_SRC_LEASE)
                if ifaces:
                    for val in ifaces.values():
                        if val['addrs']:
                            for addr in val['addrs']:
                                if addr['type'] == libvirt.VIR_IP_ADDR_TYPE_IPV4:
                                    return addr['addr']
                net = self.conn.networkLookupByName("default")
                leases = net.DHCPLeases()
                for lease in leases:
                    if lease['hostname'] == domain_name:
                        return lease['ipaddr']
            except libvirt.libvirtError:
                pass
            sleep(wait_seconds)
        return None

    def wait_for_ssh(self, ip, retries=30, delay=10):
        for attempt in range(retries):
            try:
                with paramiko.SSHClient() as client:
                    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                    client.connect(ip, username=self.ssh_user, password=self.ssh_password, timeout=5)
                print(f"SSH connection to {ip} successful")
                return True
            except Exception as e:
                print(f"Attempt {attempt + 1}/{retries} for {ip} failed: {str(e)}")
                time.sleep(delay)
        return False

    def upload_and_run_script(self, ip, script, gui=False):
        if not os.path.exists(script):
            print(f"Script {script} not found, skipping for {ip}")
            return False
        if not self.wait_for_ssh(ip):
            print(f"Failed to establish SSH connection to {ip}")
            return False
        try:
            with paramiko.SSHClient() as client:
                client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                client.connect(ip, username=self.ssh_user, password=self.ssh_password)
                with client.open_sftp() as sftp:
                    remote_path = f"/root/{os.path.basename(script)}"
                    sftp.put(script, remote_path)
                    sftp.chmod(remote_path, 0o755)
                stdin, stdout, stderr = client.exec_command(
                    f"test -f ~/.setup_done && echo 'SKIPPED' || (echo '{self.ssh_password}' | sudo -S bash {os.path.basename(script)} && touch ~/.setup_done)",
                    get_pty=True
                )
                output = stdout.read().decode().strip()
                error = stderr.read().decode().strip()
                if "SKIPPED" in output:
                    print(f"Setup already completed on {ip}")
                else:
                    print(f"Setup completed on {ip}")
                if error:
                    print(f"Error on {ip}: {error}")
                    return False
                return True
        except Exception as e:
            print(f"Failed to setup {ip}: {str(e)}")
            return False

    def setup_environment(self):
        try:
            if not self.conn:
                self.connect_libvirt()
            if self.rebuild:
                for node in self.nodes:
                    try:
                        if self.check_vm_exists(node):
                            print(f"Undefining and removing storage for {node}...")
                            os.system(f"sudo virsh undefine {node} --remove-all-storage")
                            os.system(f"rm -f {self.nodes[node]['image']}")
                        else:
                            print(f"{node} does not exist, skipping undefine.")
                    except Exception as e:
                        print(f"Error while undefining {node}: {str(e)}")
            print("Creating disk clones...")
            self.create_clones()
            print("\nCreating virtual machines...")
            self.create_vms()
            print("\nWaiting for VMs to boot and get IP addresses...")
            sleep(180)
            for node in self.nodes:
                print(f"Waiting for {node} IP assignment...")
                ip = None
                for _ in range(30):
                    ip = self.get_vm_ip(node)
                    if ip:
                        self.nodes[node]["ip"] = ip
                        print(f"{node} got IP: {ip}")
                        break
                    sleep(10)
                if not ip:
                    print(f"Warning: Could not get IP for {node}")
            print("\nRunning setup scripts...")
            for node, details in self.nodes.items():
                if not details["ip"]:
                    print(f"Skipping {node} - no IP address assigned")
                    continue
                print(f"\nSetting up {node} ({details['ip']})...")
                self.upload_and_run_script(details["ip"], details["script"], gui=details["gui"])
            print("\nEnvironment setup completed successfully!")
            return True
        except Exception as e:
            print(f"\nError during environment setup: {str(e)}")
            return False
        finally:
            self.close_libvirt()


if __name__ == "__main__":
    env = Environment(
        base_image="/home/nitu/noble_base.qcow2",
        ssh_user="root",
        ssh_password="ubuntu",
        scripts_dir="/home/nitu/Programs/projectSem6/eklavya-alpha/network/sample_env/env1",
        rebuild=True
    )
    if not env.upload_and_run_script("192.168.122.15", "/home/nitu/Programs/projectSem6/eklavya-alpha/network/sample_env/env1/3.sh"):
        sys.exit(1)
