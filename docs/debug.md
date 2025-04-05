# How to troubleshoot Yum Extender

## Run yumex i debug mode

```
yumex -d
```

**NOTE: development build always run in debug mode**

### Debug log files

Debug log messages will be written to terminal and into ~/.local/share/yumex/yumex_debug.log

The log file will be rotated for five generation yumex_debug.log.x (x=1-5)

### Tracebacks

Exceptions will be shown i a dialog and written to ~/.local/share/yumex/traceback*\<date\>*\<time\>.txt files

# Reporting issues

You can report issues on [github](https://github.com/timlau/yumex-ng/issues)

Before reporting, please check the latest development

[yumex-ng-dev](https://copr.fedorainfracloud.org/coprs/timlau/yumex-ng-dev/)

## Debug dnf5daemon-server

### monitor signals

```
sudo dbus-monitor "type='signal',sender='org.rpm.dnf.v0'"
```

### follow dnf5daemon-server logs

```
journalctl -f -u dnf5daemon-server
```
