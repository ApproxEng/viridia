# Linux Support

Scripts, in particular init scripts, used to invoke the Python code on the Pi

To install, from this directory, run the following as root on the Pi:

```bash
cp viridia /etc/init.d/viridia
chmod a+x /etc/init.d/viridia
chmod a+x ../scripts/viridia_service.py
update-rc.d viridia defaults 
```
