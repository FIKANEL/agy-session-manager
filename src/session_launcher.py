"""
session_launcher.py - Build arguments and launch Agy CLI for session resume.
"""
import os
import subprocess
from typing import Optional, List, Tuple
from dataclasses import dataclass


@dataclass
class LaunchConfig:
    conversation_id: str = ""
    working_directory: str = ""
    skip_permissions: bool = False
    agy_executable: str = ""
    terminal: str = "wt"  # "wt" for Windows Terminal, "powershell" fallback
    executable: str = ""  # alias for agy_executable for compatibility

    def __post_init__(self):
        if self.executable and not self.agy_executable:
            self.agy_executable = self.executable
        elif self.agy_executable and not self.executable:
            self.executable = self.agy_executable


class LaunchError(Exception):
    pass


def validate_conversation_id(cid: str) -> bool:
    """Validate that a conversation ID looks like a valid UUID."""
    import re
    pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
    return bool(re.match(pattern, cid.lower()))


def build_launch_args(config: LaunchConfig) -> List[str]:
    """Build the argument list for launching Agy CLI."""
    if not config.agy_executable:
        raise LaunchError("Agy CLI executable not configured")

    if not config.conversation_id:
        raise LaunchError("No conversation ID specified")

    if not validate_conversation_id(config.conversation_id):
        raise LaunchError(
            f"Invalid conversation ID format: {config.conversation_id}"
        )

    args = [config.agy_executable]
    args.append(f"--conversation={config.conversation_id}")

    if config.skip_permissions:
        args.append("--dangerously-skip-permissions")

    return args


def build_command_string(config: LaunchConfig) -> str:
    """Build a display-friendly command string."""
    args = build_launch_args(config)
    return " ".join(args)


def find_terminal(preference: str = "auto") -> Tuple[str, str]:
    """Find the best available terminal emulator based on preference.
    Returns (executable_path, terminal_type).
    """
    import shutil

    if preference == "wt":
        wt = shutil.which("wt")
        if wt:
            return wt, "wt"
    elif preference == "pwsh":
        pwsh = shutil.which("pwsh")
        if pwsh:
            return pwsh, "pwsh"
    elif preference == "powershell":
        ps = shutil.which("powershell")
        if ps:
            return ps, "powershell"

    # Auto fallback order: wt -> pwsh -> powershell -> cmd
    wt = shutil.which("wt")
    if wt:
        return wt, "wt"

    pwsh = shutil.which("pwsh")
    if pwsh:
        return pwsh, "pwsh"

    ps = shutil.which("powershell")
    if ps:
        return ps, "powershell"

    cmd = shutil.which("cmd")
    if cmd:
        return cmd, "cmd"

    raise LaunchError("No terminal emulator found")


def launch_session(config: LaunchConfig) -> subprocess.Popen:
    """Launch Agy CLI in a new terminal window."""
    if not os.path.isfile(config.agy_executable):
        raise LaunchError(
            f"Agy CLI executable not found: {config.agy_executable}"
        )

    agy_args = build_launch_args(config)
    terminal_exe, terminal_type = find_terminal(config.terminal)

    # Determine working directory
    cwd = config.working_directory
    if not cwd or not os.path.isdir(cwd):
        cwd = os.path.expanduser("~")

    # Format arguments for shell invocation safely
    formatted_args = " ".join(f'"{a}"' if " " in a else a for a in agy_args)

    if terminal_type in ("wt", "pwsh", "powershell"):
        # Use -EncodedCommand to eliminate argument parsing / quote escaping bugs in Windows Terminal & PowerShell
        import base64
        ps_script = f"Set-Location -LiteralPath '{cwd}'; & '{config.agy_executable}' " + " ".join(
            f"'{a}'" if " " in a else a for a in agy_args[1:]
        )
        encoded_cmd = base64.b64encode(ps_script.encode("utf-16le")).decode("ascii")

        if terminal_type == "wt":
            cmd = [
                terminal_exe, "-d", cwd,
                "powershell.exe", "-NoExit", "-ExecutionPolicy", "Bypass",
                "-EncodedCommand", encoded_cmd
            ]
        else:
            cmd = [
                terminal_exe, "-NoExit", "-ExecutionPolicy", "Bypass",
                "-EncodedCommand", encoded_cmd
            ]
    elif terminal_type == "cmd":
        cmd = [terminal_exe, "/K", f"cd /d {cwd} && {formatted_args}"]
    else:
        cmd = agy_args

    try:
        proc = subprocess.Popen(
            cmd,
            cwd=cwd,
            creationflags=subprocess.CREATE_NEW_CONSOLE,
        )
        return proc
    except FileNotFoundError:
        raise LaunchError(f"Failed to start terminal: {terminal_exe}")
    except PermissionError:
        raise LaunchError(
            f"Permission denied launching: {terminal_exe}"
        )
    except Exception as e:
        raise LaunchError(f"Failed to launch session: {e}")
