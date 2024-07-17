import tkinter as tk
from tkinter import messagebox
import paramiko
import os

class FileTransferApp:
    def __init__(self, master):
        self.master = master
        master.title("File Transfer App")

        self.setup_gui()

    def setup_gui(self):
        self.label = tk.Label(self.master, text="File Transfer between Linux Machines using SCP")
        self.label.pack(pady=10)

        # Source server input on the right
        self.source_server_label = tk.Label(self.master, text="Select the source server:")
        self.source_server_label.pack(pady=5)

        self.source_server_var = tk.StringVar(self.master)
        self.source_server_var.set("CERLXPT")  # Default value

        self.servers = ["DESLXPT", "CERLXPT", "CERVSPT", "SPPLXPT", "SPPVSPT", 
                        "SPPLXINT", "SPPVSINT", "PRDLXPT", "PRDVSPT", "PRDLXINT", "PRDVSINT"]

        self.source_server_menu = tk.OptionMenu(self.master, self.source_server_var, *self.servers, command=self.update_directory_list)
        self.source_server_menu.pack(pady=5)

        # Destination server input on the left
        self.destination_server_label = tk.Label(self.master, text="Select the destination server:")
        self.destination_server_label.pack(pady=5)

        self.destination_server_var = tk.StringVar(self.master)
        self.destination_server_var.set("CERVSPT")  # Default value

        self.destination_server_menu = tk.OptionMenu(self.master, self.destination_server_var, *self.servers)
        self.destination_server_menu.pack(pady=5)

        # Dropdown to select directory
        self.directory_label = tk.Label(self.master, text="Select the directory:")
        self.directory_label.pack(pady=5)

        self.directory_var = tk.StringVar(self.master)
        self.directory_menu = tk.OptionMenu(self.master, self.directory_var, "", command=self.update_file_list)
        self.directory_menu.pack(pady=5)

        # Dropdown to select file
        self.file_label = tk.Label(self.master, text="Select the file:")
        self.file_label.pack(pady=5)

        self.file_var = tk.StringVar(self.master)
        self.file_menu = tk.OptionMenu(self.master, self.file_var, "")
        self.file_menu.pack(pady=5)

        # Input for destination path
        self.dest_path_label = tk.Label(self.master, text="Enter the destination path:")
        self.dest_path_label.pack(pady=5)

        self.dest_path_entry = tk.Entry(self.master, width=50)
        self.dest_path_entry.pack(pady=5)

        # Transfer button
        self.transfer_button = tk.Button(self.master, text="Transfer File", command=self.transfer_file)
        self.transfer_button.pack(pady=10)

        # Create local directories for backup and transfer
        self.backup_dir = "local_backup"
        self.transfer_dir = "transferfiles"

        if not os.path.exists(self.backup_dir):
            os.makedirs(self.backup_dir)

        if not os.path.exists(self.transfer_dir):
            os.makedirs(self.transfer_dir)

    def update_directory_list(self, server_name):
        try:
            server_info = self.get_server_info(server_name)
            directories = self.list_directories_on_server(server_info, "/app/mf/cer")
            if directories:
                menu = self.directory_menu["menu"]
                menu.delete(0, "end")
                for directory in directories:
                    menu.add_command(label=directory, command=lambda value=directory: self.directory_var.set(value))
                self.directory_var.set(directories[0])
                self.update_file_list(directories[0])
            else:
                self.directory_var.set("")
                menu = self.directory_menu["menu"]
                menu.delete(0, "end")
                menu.add_command(label="No directories found", command=lambda: None)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to update directory list: {str(e)}")

    def update_file_list(self, directory):
        try:
            server_name = self.source_server_var.get()
            server_info = self.get_server_info(server_name)
            files = self.list_files_on_server(server_info, f"/app/mf/cer/{directory}")
            if files:
                menu = self.file_menu["menu"]
                menu.delete(0, "end")
                for file in files:
                    menu.add_command(label=file, command=lambda value=file: self.file_var.set(value))
                self.file_var.set(files[0])
            else:
                self.file_var.set("")
                menu = self.file_menu["menu"]
                menu.delete(0, "end")
                menu.add_command(label="No files found", command=lambda: None)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to update file list: {str(e)}")

    def transfer_file(self):
        source_server = self.source_server_var.get()
        destination_server = self.destination_server_var.get()
        directory = self.directory_var.get()
        source_file_path = os.path.join(f"/app/mf/cer/{directory}", self.file_var.get())
        dest_path = self.dest_path_entry.get()

        try:
            # Find and backup the file on the destination server
            self.backup_file(destination_server, source_file_path)

            # Find the file on the source server and copy it to transferfiles
            local_file_path = self.find_and_copy_file(source_server, source_file_path)

            # Upload the file from transferfiles to the destination server
            self.upload_to_server(local_file_path, destination_server, os.path.join(dest_path, os.path.basename(source_file_path)))

            messagebox.showinfo("Success", f"File transferred from {source_server} to {destination_server} successfully.")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")

    def backup_file(self, server_name, file_path):
        server_info = self.get_server_info(server_name)
        try:
            # Find the file on the destination server and download it as backup
            remote_file_path = self.find_file_on_server(server_info, file_path)
            if remote_file_path:
                local_backup_path = os.path.join(self.backup_dir, os.path.basename(file_path))
                self.download_from_server(server_info, remote_file_path, local_backup_path)
        except Exception as e:
            messagebox.showerror("Backup Error", f"Failed to backup file from {server_name}: {str(e)}")

    def find_and_copy_file(self, server_name, file_path):
        server_info = self.get_server_info(server_name)
        try:
            # Find the file on the source server and copy it to transferfiles
            remote_file_path = self.find_file_on_server(server_info, file_path)
            if remote_file_path:
                local_transfer_path = os.path.join(self.transfer_dir, os.path.basename(file_path))
                self.download_from_server(server_info, remote_file_path, local_transfer_path)
                return local_transfer_path
            else:
                raise FileNotFoundError(f"File {file_path} not found on {server_name}")
        except Exception as e:
            messagebox.showerror("Find Error", f"Failed to find file on {server_name}: {str(e)}")

    def get_server_info(self, server_name):
        # Define the connection info for each server
        servers = {
            "DESLXPT": {"hostname": "lxrhbmwd01.sys.sibs.pt", "username": "mfocus", "key_filename":"\\\\sibsharectm\\CTM_Jobs\\SSH_Keys\\mfocus_py"},
            "CERLXPT": {"hostname": "lxrhbmwc01.sys.sibs.pt", "username": "mfocus", "key_filename":"\\\\sibsharectm\\CTM_Jobs\\SSH_Keys\\mfocus_py"},
            "CERVSPT": {"hostname": "vsrhbmwc01.sys.sibs.pt", "username": "mfocus", "key_filename":"\\\\sibsharectm\\CTM_Jobs\\SSH_Keys\\mfocus_py"},
            "SPPLXPT": {"hostname": "lxrhbmwprtq01.sys.sibs.pt", "username": "mfocus", "key_filename":"\\\\sibsharectm\\CTM_Jobs\\SSH_Keys\\mfocus_py"},
            "SPPVSPT": {"hostname": "vsrhbmwprtq01.sys.sibs.pt", "username": "mfocus", "key_filename":"\\\\sibsharectm\\CTM_Jobs\\SSH_Keys\\mfocus_py"},
            "SPPLXINT": {"hostname": "lxrhbmwintq01.sys.sibs.pt", "username": "mfocus", "key_filename":"\\\\sibsharectm\\CTM_Jobs\\SSH_Keys\\mfocus_py"},
            "SPPVSINT": {"hostname": "lxrhbmwintq01.sys.sibs.pt", "username": "mfocus", "key_filename":"\\\\sibsharectm\\CTM_Jobs\\SSH_Keys\\mfocus_py"},
            "PRDLXPT": {"hostname": "lxrhbmwprtp01.sys.sibs.pt", "username": "mfocus", "key_filename":"\\\\sibsharectm\\CTM_Jobs\\SSH_Keys\\mfocus_py"},
            "PRDVSPT": {"hostname": "vsrhbmwprtp01.sys.sibs.pt", "username": "mfocus", "key_filename":"\\\\sibsharectm\\CTM_Jobs\\SSH_Keys\\mfocus_py"},
            "PRDLXINT": {"hostname": "lxrhbmwintp01.sys.sibs.pt", "username": "mfocus", "key_filename":"\\\\sibsharectm\\CTM_Jobs\\SSH_Keys\\mfocus_py"},
            "PRDVSINT": {"hostname": "vsrhbmwintp01.sys.sibs.pt", "username": "mfocus", "key_filename":"\\\\sibsharectm\\CTM_Jobs\\SSH_Keys\\mfocus_py"},
        }
        return servers.get(server_name)

    def list_directories_on_server(self, server_info, directory):
        hostname = server_info["hostname"]
        username = server_info["username"]
        key_filename = server_info["key_filename"]

        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname, username=username, key_filename=key_filename)

        stdin, stdout, stderr = ssh.exec_command(f"ls -d {directory}/*/")
        directories = [dir.rstrip('/') for dir in stdout.read().decode().split()]

        ssh.close()
        return directories

    def list_files_on_server(self, server_info, directory):
        hostname = server_info["hostname"]
        username = server_info["username"]
        key_filename = server_info["key_filename"]

        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname, username=username, key_filename=key_filename)

        stdin, stdout, stderr = ssh.exec_command(f"ls {directory}")
        files = stdout.read().decode().split()

        ssh.close()
        return files

    def find_file_on_server(self, server_info, file_path):
        hostname = server_info["hostname"]
        username = server_info["username"]
        key_filename = server_info["key_filename"]

        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname, username=username, key_filename=key_filename)

        stdin, stdout, stderr = ssh.exec_command(f"find / -type f -name '{os.path.basename(file_path)}' 2>/dev/null")
        remote_file_path = stdout.readline().strip()

        ssh.close()

        return remote_file_path

    def download_from_server(self, server_info, remote_path, local_path):
        hostname = server_info["hostname"]
        username = server_info["username"]
        key_filename = server_info["key_filename"]

        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname, username=username, key_filename=key_filename)

        scp = paramiko.SFTPClient.from_transport(ssh.get_transport())
        scp.get(remote_path, local_path)

        scp.close()
        ssh.close()

    def upload_to_server(self, local_path, server_name, remote_path):
        server_info = self.get_server_info(server_name)
        hostname = server_info["hostname"]
        username = server_info["username"]
        key_filename = server_info["key_filename"]

        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname, username=username, key_filename=key_filename)

        sftp = ssh.open_sftp()
        sftp.put(local_path, remote_path)
        sftp.close()
        ssh.close()

if __name__ == "__main__":
    root = tk.Tk()
    app = FileTransferApp(root)
    root.mainloop()

