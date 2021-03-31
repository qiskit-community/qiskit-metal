import asyncio

# import asyncio
#
# async def run(cmd):
#     proc = await asyncio.create_subprocess_shell(
#         cmd,
#         stdout=asyncio.subprocess.PIPE,
#         stderr=asyncio.subprocess.PIPE)
#
#     stdout, stderr = await proc.communicate()
#
#     print(f'[{cmd!r} exited with {proc.returncode}]')
#     if stdout:
#         print(f'[stdout]\n{stdout.decode()}')
#     if stderr:
#         print(f'[stderr]\n{stderr.decode()}')
#
# asyncio.run(run('ls /zzz'))
# 'ls /zzz' exited with 1]
# [stderr]
# ls: /zzz: No such file or directory


#  shlex.quote() https://en.wikipedia.org/wiki/Code_injection#Shell_injection


import pathlib
current_running_file = pathlib.Path(__file__).parent.absolute()
cwd = pathlib.Path().absolute()

import subprocess
import pathlib
import os.path as path

current_running_file = pathlib.Path(__file__).parent.absolute()
cwd = pathlib.Path().absolute()

# check if darwin
# clang -framework Foundation hello.m -o hello

MAC = './macos_editors/main'
vs_code = "com.microsoft.VSCode"


def get_mac_app(name: str):
    cmd = f'{MAC} {vs_code}'
    proc = subprocess.Popen([MAC, vs_code],
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            cwd=current_running_file)
    print("about to run: ", cmd)
    stdout, stderr = proc.communicate()
    print(f'[{cmd!r} exited with {proc.returncode}]')

    if stderr:
        raise Exception("ERRORED: " + stderr.decode())
    full_path = stdout.decode().strip()

    print("full path: ", full_path)
    if path.isdir(full_path):
        print(f"{full_path} exists!")
    else:
        print(f"{full_path} does NOT exist!")
        return

        # open_editor_cmd = f'open -a {full_path} {FILE}'
    # print("running... " + open_editor_cmd)
    print(f"typ: {type(full_path)}")
    full_path_shell = full_path
    print(f"full path {full_path} \n fullshell : {full_path_shell}")
    editproc = subprocess.Popen(
        ['open', '-a', full_path_shell, name],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=current_running_file)
    stdout, stderr = editproc.communicate()
    print(f"stdout: {stdout} stderr: {stderr}")


#asyncio.run(get_mac_app())
