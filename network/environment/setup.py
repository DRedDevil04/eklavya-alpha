import os
import time
import libvirt
import paramiko

class Environment:
    def __init__(self, base_image, ssh_user, ssh_password):
        """Initialize environment settings."""
        self.base_image = base_image
        self.ssh_user = ssh_user
        self.ssh_password = ssh_password
        self.nodes = {
            "node1-linux": {"image": "/var/lib/libvirt/images/node1.qcow2", "script": "1.sh", "ip": "192.168.122.101"},
            "node2-linux": {"image": "/var/lib/libvirt/images/node2.qcow2", "script": "2.sh", "ip": "192.168.122.102"},
            "node3-linux": {"image": "/var/lib/libvirt/images/node3.qcow2", "script": "3.sh", "ip": "192.168.122.103"},
        }
        self.vm_template = """
        <domain type='kvm'>
          <name>{name}</name>
          <memory unit='MiB'>2048</memory>
          <vcpu placement='static'>2</vcpu>
          <os>
            <type arch='x86_64'>hvm</type>
          </os>
          <devices>
            <disk type='file' device='disk'>
              <driver name='qemu' type='qcow2'/>
              <source file='{image}'/>
              <target dev='vda' bus='virtio'/>
            </disk>
            <interface type='network'>
              <source network='default'/>
              <model type='virtio'/>
            </interface>
            <graphics type='vnc' port='-1' autoport='yes'/>
          </devices>
        </domain>
        """

    def create_clones(self):
        """Create VM clones from the base image."""
        for i in range(1,4):
            os.system(f"qemu-img create -f qcow2 -b ~/noble_base.qcow2 -F qcow2 /network/env_data/ubuntu-node{i}.qcow2")

    def create_vms(self):
        """Define and start virtual machines using libvirt."""
        conn = libvirt.open("qemu:///system")
        for node, details in self.nodes.items():
            xml_config = self.vm_template.format(name=node, image=details["image"])
            print(f"Creating {node}...")
            domain = conn.defineXML(xml_config)
            domain.create()
        conn.close()
        print("All VMs started successfully.")

    def wait_for_ssh(self, ip, retries=10, delay=10):
        """Wait until SSH is available."""
        for _ in range(retries):
            try:
                client = paramiko.SSHClient()
                client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                client.connect(ip, username=self.ssh_user, password=self.ssh_password, timeout=5)
                client.close()
                return True
            except:
                print(f"Waiting for {ip} to be reachable...")
                time.sleep(delay)
        return False

    def upload_and_run_script(self, ip, script):
        """Upload and execute the setup script."""
        if not self.wait_for_ssh(ip):
            print(f"Failed to reach {ip}, skipping setup.")
            return

        try:
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(ip, username=self.ssh_user, password=self.ssh_password)

            sftp = client.open_sftp()
            remote_path = f"/home/{self.ssh_user}/{script}"
            sftp.put(script, remote_path)
            sftp.chmod(remote_path, 0o755)
            sftp.close()

            stdin, stdout, stderr = client.exec_command(f"test -f ~/.setup_done && echo 'SKIPPED' || (./{script} && touch ~/.setup_done)")
            output = stdout.read().decode().strip()
            error = stderr.read().decode().strip()

            if "SKIPPED" in output:
                print(f"{script} already executed on {ip}. Skipping.")
            else:
                print(f"Executed {script} on {ip}.")

            if error:
                print(f"Error on {ip}: {error}")

            client.close()
        except Exception as e:
            print(f"Failed to setup {ip}: {e}")

    def setup_environment(self):
        """Main method to set up the entire environment."""
        self.create_clones()
        self.create_vms()

        print("Waiting for VMs to boot up...")
        time.sleep(60)  # Allow VMs to initialize

        for node, details in self.nodes.items():
            self.upload_and_run_script(details["ip"], details["script"])


if __name__ == "__main__":
    env = Environment(
        base_image="/var/lib/libvirt/images/noble.qcow2",
        ssh_user="devam",
        ssh_password="your_ssh_password"  # Replace with SSH key authentication for security
    )
    env.setup_environment()
