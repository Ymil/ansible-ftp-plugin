import difflib
import os
import pathlib
import shutil
from ftplib import FTP

from ansible.plugins.action import ActionBase


class FTPManager:

    def __init__(self, host, username, password):
        self.host = host
        self.username = username
        self.password = password
        self.local_dir = '.tmp/'
        self.remote_dir = ''
        self._connect()
        self.set_local_path(self.local_dir)

    def _connect(self):
        self._con = FTP(
            host=self.host,
            user=self.username, passwd=self.password,
        )
        self._con.encoding = 'utf-8'
        self.remote_dir = self._con.pwd()

    def set_remote_path(self, path):
        try:
            self._con.cwd(path)
        except Exception as e:
            raise Exception(f'Could not set remote path to {path}\n{e}')
        self.remote_dir = path

    def set_local_path(self, path):
        self.local_dir = path
        if not os.path.exists(self.local_dir):
            os.makedirs(self.local_dir)
        else:
            shutil.rmtree(self.local_dir)
            os.makedirs(self.local_dir)

    def download(self, remote_filename, local_filename='') -> list:
        try:
            if not len(local_filename):
                local_filename = remote_filename
            local_path = os.path.join(self.local_dir, local_filename)
            with open(local_path, 'wb') as f:
                self._con.retrbinary(f'RETR {remote_filename}', f.write)
            return [remote_filename]
        except Exception as e:
            raise Exception(f'Could not download {remote_filename}\n{e}')

    def download_folder(self, path='') -> list:
        try:
            if len(path):
                self._con.cwd(path)

            local_path = os.path.join(self.local_dir, path)
            os.makedirs(local_path, exist_ok=True)

            file_list = self._con.nlst()

            download_files_list = []
            for file_name in file_list:

                if path == '':
                    file_name_absolute = file_name
                else:
                    file_name_absolute = f'{path}/{file_name}'

                if self.__is_ftp_dir(file_name):
                    download_files_list += self.download_folder(
                        f'{file_name_absolute}',
                    )
                    self._con.cwd('..')
                else:
                    self.download(file_name, file_name_absolute)
                    download_files_list.append(
                        f'{self.local_dir}/{file_name_absolute}',
                    )

            return download_files_list
        except Exception as e:
            raise Exception(f"Could not download folder '{path}' \n {e}")

    def __is_ftp_dir(self, file_name):
        original_cwd = self._con.pwd()
        try:
            self._con.cwd(file_name)
            self._con.cwd(original_cwd)
            return True
        except:  # noqa
            return False

    def upload(self, local_filename, remote_filename):
        # Check if folders exists and create if not

        folders = remote_filename.split('/')[:-1]
        filename = remote_filename.split('/')[-1]
        for folder in folders:
            # Check if folder is folder
            if folder is not filename:
                if self.__is_ftp_dir(folder):
                    self._con.cwd(folder)
                else:
                    self._con.mkd(folder)
                    self._con.cwd(folder)

        try:
            with open(local_filename, 'rb') as f:
                self._con.storbinary(f'STOR {filename}', f)
                self._con.cwd(self.remote_dir)
        except Exception as e:
            raise Exception(fr'Could not upload {local_filename}\ņ{e}')


def compare_files(local_files, ftp_files, output_diff):
    local_files_without_absolute = [
        '/'.join(str(file).split('/')[1:]) for file in local_files
    ]
    local_files = list(zip(local_files, local_files_without_absolute))

    ftp_files_without_absolute = [
        '/'.join(str(file).split('/')[1:]) for file in ftp_files
    ]
    ftp_files = list(zip(ftp_files, ftp_files_without_absolute))

    files_diffs = []
    diff_all = ''
    for local_file_absolute, local_file_relative in local_files:
        remote_file = list(
            filter(lambda file: file[1] == local_file_relative, ftp_files),
        )
        if not len(remote_file):
            files_diffs.append((local_file_absolute, local_file_relative))
            diff = difflib.unified_diff(
                [local_file_relative], [
                ], fromfile=f'local/{local_file_relative}',
                tofile=f'ftp/{local_file_relative}',
            )
            diff_all += ''.join(diff)
            continue
        else:
            remote_file_absolute = str(remote_file[0][0])
            diff = difflib.unified_diff(
                open(f'{local_file_absolute}').readlines(),
                open(f'{remote_file_absolute}').readlines(),
                fromfile=f'local/{local_file_relative}',
                tofile=f'ftp/{local_file_relative}',
            )
            diff = list(diff)
            diff_all += ''.join(diff)
            if len(list(diff)) > 0:
                files_diffs.append((local_file_absolute, local_file_relative))
    with open(output_diff, 'w') as f:
        f.writelines(diff)
    return files_diffs


def get_local_files(local_dir):
    files = list(pathlib.Path(local_dir).rglob('*'))
    files = filter(lambda x: os.path.isfile(x), files)
    # files = [str(file).replace(local_dir + '/', '') for file in files]
    return list(files)


class ActionModule(ActionBase):
    def run(self, tmp=None, task_vars=None):
        super().run(tmp, task_vars)
        result = {
            'changed': False,
            'msg': '',
            'diff': {
                'files': [],
            },
        }

        ftp_host = task_vars.get('ftp_host')
        ftp_user = task_vars.get('ftp_user')
        ftp_password = str(task_vars.get('ftp_password'))
        remote_path = self._task.args.get('remote_path', '')
        local_path = self._task.args.get('local_path', '')

        if not (ftp_host and ftp_user and ftp_password):
            result['msg'] = 'Missing required parameters'
            return result

        ftp = FTPManager(ftp_host, ftp_user, ftp_password)
        local_files = get_local_files(local_path)
        ftp.set_local_path('.tmp')
        ftp.set_remote_path(remote_path)
        ftp_files = ftp.download_folder()
        file_diff = 'diff.txt'
        files_diff = compare_files(local_files, ftp_files, file_diff)

        if len(files_diff):
            result['changed'] = True
            result['msg'] = 'Files changed. Diff Save in ' + file_diff
            # result['diff']['files'] = files_diff
            with open(file_diff) as f:
                result['diff'] = f.readlines()

                if self._task._diff:
                    print(''.join(result['diff']))

            if self._play_context.check_mode:
                return result

            for local_file_absolute, local_file_relative in files_diff:
                ftp.upload(local_file_absolute, local_file_relative)

        return result


if __name__ == '__main__':
    ftp = FTPManager('localhost', 'one', '1234')
    local_files = get_local_files('local_files/')
    ftp.set_local_path('.tmp')
    ftp_files = ftp.download_folder()
    print(local_files, ftp_files)
    compare_files(local_files, ftp_files, 'diff.txt')
