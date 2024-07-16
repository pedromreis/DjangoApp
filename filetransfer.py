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

        self.source_server_label = tk.Label(self.master, text="Select the source server:")
        self.source_server_label.pack(pady=5)

        self.source_server_var = tk.StringVar(self.master)
        self.source_server_var.set("Server 1")  # Default value

        self.servers = ["Server 1", "Server 2", "Server 3", "Server 4", "Server 5", 
                        "Server 6", "Server 7", "Server 8", "Server 9", "Server 10", "Server 11"]

        self.source_server_menu = tk.OptionMenu(self.master, self.source_server_var, *self.servers, command=self.update_source_file_list)
        self.source_server_menu.pack(pady=5)

        self.destination_server_label = tk.Label(self.master, text="Select the destination server:")
        self.destination_server_label.pack(pady=5)

        self.destination_server_var = tk.StringVar(self.master)
        self.destination_server_var.set("Server 2")  # Default value

        self.destination_server_menu = tk.OptionMenu(self.master, self.destination_server_var, *self.servers, command=self.update_dest_dir_list)
        self.destination_server_menu.pack(pady=5)

        self.source_file_label = tk.Label(self.master, text="Select the source file or folder:")
        self.source_file_label.pack(pady=5)

        self.source_file_var = tk.StringVar(self.master)
        self.source_file_var.set("")

        self.source_file_menu = tk.OptionMenu(self.master, self.source_file_var, "")
        self.source_file_menu.pack(pady=5)

        self.dest_path_label = tk.Label(self.master, text="Select the destination path:")
        self.dest_path_label.pack(pady=5)

        self.dest_path_var = tk.StringVar(self.master)
        self.dest_path_var.set("/app/mf/cer/data")

        self.dest_path_menu = tk.OptionMenu(self.master, self.dest_path_var, "")
        self.dest_path_menu.pack(pady=5)

        self.transfer_button = tk.Button(self.master, text="Transfer File", command=self.transfer_file)
        self.transfer_button.pack(pady=10)

        self.backup_dir = "local_backup"
        self.transfer_dir = "transferfiles"

        if not os.path.exists(self.backup_dir):
            os.makedirs(self.backup_dir)

        if not os.path.exists(self.transfer_dir):
            os.makedirs(self.transfer_dir)

        # Inicializa a navegação na pasta inicial
        self.update_source_file_list(self.source_server_var.get())
        self.update_dest_dir_list(self.destination_server_var.get())

    def update_source_file_list(self, server_name):
        self.update_file_list(server_name, self.source_file_menu, self.source_file_var, "/app/mf/cer/data", False)

    def update_dest_dir_list(self, server_name):
        self.update_file_list(server_name, self.dest_path_menu, self.dest_path_var, "/app/mf/cer/data", True)

    def update_file_list(self, server_name, menu_widget, var_widget, directory, is_directory):
        try:
            server_info = self.get_server_info(server_name)
            files, directories = self.list_files_and_dirs_on_server(server_info, directory)
            menu = menu_widget["menu"]
            menu.delete(0, "end")

            # Adiciona a opção de voltar para a pasta anterior
            parent_dir = os.path.dirname(directory.rstrip('/'))
            if parent_dir:
                menu.add_command(label=".. (Up)", command=lambda: self.update_file_list(server_name, menu_widget, var_widget, parent_dir, is_directory))

            if directories:
                for dir in directories:
                    menu.add_command(label=f"[D] {dir}", command=lambda value=dir: self.update_file_list(server_name, menu_widget, var_widget, os.path.join(directory, value), is_directory))

            if files:
                for file in files:
                    menu.add_command(label=file, command=lambda value=os.path.join(directory, value): var_widget.set(value))
            
            var_widget.set(directory if is_directory else "")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to update file list: {str(e)}")

    def transfer_file(self):
        source_server = self.source_server_var.get()
        destination_server = self.destination_server_var.get()
        source_file_path = self.source_file_var.get()
        dest_path = self.dest_path_var.get()

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
        # Define as informações de conexão para cada servidor
        servers = {
            "Server 1": {"hostname": "server1.example.com", "username": "user1", "password": "pass1"},
            "Server 2": {"hostname": "server2.example.com", "username": "user2", "password": "pass2"},
            "Server 3": {"hostname": "server3.example.com", "username": "user3", "password": "pass3"},
            "Server 4": {"hostname": "server4.example.com", "username": "user4", "password": "pass4"},
            "Server 5": {"hostname": "server5.example.com", "username": "user5", "password": "pass5"},
            "Server 6": {"hostname": "server6.example.com", "username": "user6", "password": "pass6"},
            "Server 7": {"hostname": "server7.example.com", "username": "user7", "password": "pass7"},
            "Server 8": {"hostname": "server8.example.com", "username": "user8", "password": "pass8"},
            "Server 9": {"hostname": "server9.example.com", "username": "user9", "password": "pass9"},
            "Server 10": {"hostname": "server10.example.com", "username": "user10", "password": "pass10"},
            "Server 11": {"hostname": "server11.example.com", "username": "user11", "password": "pass11"},
        }
        return servers.get(server_name)

    def list_files_and_dirs_on_server(self, server_info, directory):
        hostname = server_info["hostname"]
        username = server_info["username"]
        password = server_info["password"]

        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname, username=username, password=password)

        sftp = ssh.open_sftp()
        files = []
        directories = []

        for item in sftp.listdir_attr(directory):
            item_name = item.filename
            if stat.S_ISDIR(item.st_mode):
                directories.append(item_name)
            else:
                files.append(item_name)

        sftp.close()
        ssh.close()

        return files, directories

    def find_file_on_server(self, server_info, file_path):
        hostname = server_info["hostname"]
        username = server_info["username"]
        password = server_info["password"]

        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname, username
