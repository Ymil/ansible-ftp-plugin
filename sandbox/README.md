# Ansible sandbox

En este directorio se encuentra una estrucutra de ansible para tener de ejemplo y poder probar el plugin.

Para poder ejecutarlo es necesario iniciar un servidor FTP con el siguiente comando
```bash
docker run -d -p 21:21 -p 21000-21010:21000-21010 -e USERS="one|1234" delfer/alpine-ftp-server
```

Luego puede lanzar el playbook con el siguiente comando
```bash
ansible-playbook -i inventory main.yaml -D -vvv
```
