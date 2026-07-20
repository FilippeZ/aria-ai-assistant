import sys, os

old_stdout_fd = os.dup(1)
os.dup2(2, 1)

print("This should go to stderr!")

os.dup2(old_stdout_fd, 1)
os.close(old_stdout_fd)

print("This should go to stdout!")
