import subprocess

password = "admin-super-secret"

def calculate(expression):
    print("debug expression:", expression)
    subprocess.run("echo " + expression, shell=True)
    return eval(expression)
