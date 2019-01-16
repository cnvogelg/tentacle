"""Trigger external commands."""

import os
import subprocess
import logging


class Commands:
    """Trigger external commands."""

    def __init__(self, cfg):
        """Create a commands object."""
        self._reboot_cmd = None
        self._poweroff_cmd = None
        self._restart_cmd = None
        self._backlight_on_cmd = None
        self._backlight_off_cmd = None
        # state
        self._backlight = False
        self._configure(cfg)
        self.backlight_on()

    def _configure(self, cfg):
        if 'commands' in cfg:
            cmds = cfg['commands']
            if 'restart_octoprint' in cmds:
                self._restart_cmd = cmds['restart_octoprint']
            if 'reboot_sys' in cmds:
                self._reboot_cmd = cmds['reboot_sys']
            if 'poweroff_sys' in cmds:
                self._poweroff_cmd = cmds['poweroff_sys']
            if 'backlight_on' in cmds:
                self._backlight_on_cmd = cmds['backlight_on']
            if 'backlight_off' in cmds:
                self._backlight_off_cmd = cmds['backlight_off']

    def _run_cmd(self, cmd):
        if cmd:
            args = cmd.split()
            rel_dir = os.path.join(os.path.dirname(__file__), "..")
            sys_dir = os.path.abspath(rel_dir)
            for i, arg in enumerate(args):
                if arg.startswith("./"):
                    args[i] = sys_dir + arg[1:]
            try:
                ret = subprocess.call(args)
            except IOError as exc:
                logging.error("run_cmd: %r -> %s", args, exc)
                return 1
            if ret == 0:
                logging.info("run_cmd: %r", args)
            else:
                logging.error("run_cmd: %r -> %d", args, ret)
            return ret
        else:
            return 0

    def backlight_toggle(self):
        """Toggle the backlight of the TFT display."""
        if self._backlight:
            self.backlight_off()
        else:
            self.backlight_on()

    def backlight_on(self):
        """Enable backlight of TFT display."""
        if not self._backlight:
            ret = self._run_cmd(self._backlight_on_cmd)
            logging.info("backlight on: ret=%d", ret)
            if ret == 0:
                self._backlight = True
        else:
            logging.info("backlight already on!")

    def backlight_off(self):
        """Disable backlight of TFT display."""
        if self._backlight:
            ret = self._run_cmd(self._backlight_off_cmd)
            logging.info("backlight off: ret=%d", ret)
            if ret == 0:
                self._backlight = False
        else:
            logging.info("backlight already off!")

    def restart_octoprint(self):
        """Restart OctoPrint server."""
        logging.info("restarting OctoPrint...")
        self._run_cmd(self._restart_cmd)

    def reboot_system(self):
        """Rebooting system."""
        logging.info("rebooting system...")
        self._run_cmd(self._reboot_cmd)

    def poweroff_system(self):
        """Poweroff system."""
        logging.info("powering off system...")
        self._run_cmd(self._poweroff_cmd)
