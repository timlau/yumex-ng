# Test that everything is working properly

## Test Case 01

- Select Packages (Alt+1)
- type **ffff**
- select the 0\xFFFF package (Ctrl+Space)
- Apply the changes (Ctrl+Return)
- Confirm the transaction (Ctrl+Return)
- Enter PolicyKit password
- After the transaction is completed, repeat to uninstall the 0\xFFFF package

## Test Case 02

- Install a flatpak (Ctrl+i)
- type **cont**
- use Ctrl+G and Shift+Ctrl+G to toogle search results
- select the Contrast flatpak
- Confirm the selection (Ctrl+Return)
- Confirm the transaction (Ctrl+Return)
- Contrast should be on the list of installed flatpaks
- Uninstall the Contrast flatpak, by clicking on the trashcan button left of the flatpak in the list
- Confirm the transaction (Ctrl+Return)
- Contrast should no longer be on the list of installed flatpaks


## Test Updater
### Check service
```bash
systemctl --user status yumex-updater-systray.service
```
### Check log
```bash
journalctl --user-unit=yumex-updater-systray -n 20
```
