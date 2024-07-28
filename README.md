# Ansible FTP Plugin

Este plugin de Ansible te permite revisar configuraciones utilizando FTP en lugares donde las conexiones SSH no están disponibles.

## Instalación

1. Copia el plugin en la carpeta `ansible_plugins/action_plugins`.

2. Configura el plugin en el archivo `ansible.cfg` añadiendo la siguiente línea:

    [defaults]
    action_plugins = ansible_plugins/action_plugins

## Uso

Para usar este plugin, asegúrate de que tu archivo de configuración de Ansible (`ansible.cfg`) esté correctamente configurado como se indica en la sección de instalación.

### Ejemplo de Uso

Consulta la carpeta `sandbox`, donde se encuentra un ejemplo completo de uso del plugin. Esta carpeta contiene ejemplos prácticos y guías detalladas para ayudarte a comenzar.
