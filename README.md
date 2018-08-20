# First Time Connection Setup #

When Whonix starts for the first time, it won't automatically connect to the
public Tor network. This is useful for users who want to hide Tor from their
ISP. whonixsetup is automatically started, which educates about different
methods to connect (public Tor network, bridges, etc.).

Also automatically starts the Whonix Repository Tool (if installed), so the
user can decide whether to use Whonix's Repository and if yes, choose which
one.
## How to install `whonix-setup-wizard` using apt-get ##

1\. Add [Whonix's Signing Key](https://www.whonix.org/wiki/Whonix_Signing_Key).

```
sudo apt-key --keyring /etc/apt/trusted.gpg.d/whonix.gpg adv --keyserver hkp://ipv4.pool.sks-keyservers.net:80 --recv-keys 916B8D99C38EAF5E8ADC7A2A8D66066A2EEACCDA
```

3\. Add Whonix's APT repository.

```
echo "deb http://deb.whonix.org stretch main" | sudo tee /etc/apt/sources.list.d/whonix.list
```

4\. Update your package lists.

```
sudo apt-get update
```

5\. Install `whonix-setup-wizard`.

```
sudo apt-get install whonix-setup-wizard
```

## How to Build deb Package ##

Replace `apparmor-profile-torbrowser` with the actual name of this package with `whonix-setup-wizard` and see [instructions](https://www.whonix.org/wiki/Dev/Build_Documentation/apparmor-profile-torbrowser).

## Contact ##

* [Free Forum Support](https://forums.whonix.org)
* [Professional Support](https://www.whonix.org/wiki/Professional_Support)

## Payments ##

`whonix-setup-wizard` requires [payments](https://www.whonix.org/wiki/Payments) to stay alive!
