# Serviço para remover o dirty bit do windows travando HD de escrita
Baixa o pacote: `ntfs-3g` (ex: sudo apt insntall ntfs-3g, sudo dnf install ntfs-3g,...)

Pega UUID do disco que tá travando ao iniciar
```shell
lsblk -f
```

Modifique o `ntfsfix-hdd.service` com o UUID do seu disco

```shell
nano ntfsfix-hdd.service
```

```shell
sudo mv ntfsfix-hdd.service /etc/systemd/system/ntfsfix-hdd.service
```

- - -

### Ativar serviço
```shell
sudo systemctl daemon-reload
sudo systemctl enable ntfsfix-hdd.service
```
---
### Testar sem reiniciar
```shell
sudo systemctl start ntfsfix-hdd.service
systemctl status ntfsfix-hdd.service
```
## Montagem fixa

```shell
sudo mkdir -p /mnt/volume1tb
```


```shell
sudo nano /etc/fstab
```

```fstab
UUID=SEU-UUID-AQUI  /mnt/volume1tb  ntfs-3g  defaults,uid=1000,gid=1000,umask=022  0  0
```
### Testa sem reiniciar
```shell
sudo mount -a
```

# Demais scripts
```shell
sudo copy usr/local/bin* /usr/local/bin/
sudo chmod 755 /usr/local/bin/*
```
