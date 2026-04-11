import sys

from selfsnap.runtime_launch import ensure_local_repository_interpreter


redirected_exit_code = ensure_local_repository_interpreter(sys.argv[1:])
if redirected_exit_code is not None:
    raise SystemExit(redirected_exit_code)

from selfsnap.cli import main


if __name__ == "__main__":
    raise SystemExit(main())

