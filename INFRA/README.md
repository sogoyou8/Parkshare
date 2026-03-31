Project Parkshare - Infrastructure & Deployment
Ce dépôt contient l'ensemble de l'application Parkshare ainsi que la configuration de l'infrastructure virtualisée sous Proxmox.

Architecture Globale
L'infrastructure repose sur une machine virtuelle isolée au sein d'un environnement Proxmox, sécurisée par un pare-feu et un Reverse Proxy.

Hyperviseur : Proxmox VE

OS Invité : Debian 12 (Installation persistante)

Réseau : Bridge privé (vmbr1) avec NAT/Port-Forwarding vers l'IP publique.

Conteneurisation : Docker & Docker Compose.

Composants de l'Infrastructure
1. Virtualisation & Réseau
VM Debian : 4 vCPUs, 4 Go RAM, 32 Go SSD.

Redirection de ports (iptables) :

2222 -> 22 (Accès SSH sécurisé)

80 & 443 -> 80 & 443 (Trafic Web via Reverse Proxy)

81 -> 81 (Interface d'administration Nginx Proxy Manager)

2. Stack Logicielle (Docker)
L'application est orchestrée via Docker Compose pour garantir l'isolation des services :

Nginx Proxy Manager (NPM) : Gère le nom de domaine, le routage et les certificats SSL (Let's Encrypt).

Parkshare App : Image Python 3.11-slim exécutant le Dashboard Streamlit.


Installation et Déploiement
Pré-requis
Docker & Docker Compose installés sur la VM.

Accès SSH à la VM.

Procédure de déploiement
Cloner le dépôt :

Bash
git clone https://github.com/sogoyou8/Parkshare.git
cd Parkshare/INFRA
Lancer les services :

Bash
docker-compose up -d --build
Configuration du domaine :

Accéder à l'interface NPM : http://<IP_PUBLIQUE>:81

Créer un Proxy Host pour parkshare-ynov.duckdns.org.


Sécurité & Optimisations
Isolation : L'application tourne dans un conteneur non-privilégié.

Optimisation Python : Utilisation d'images Docker slim pour réduire l'empreinte disque.


🌐 Accès Public
L'application est accessible à l'adresse suivante :
http://parkshare-ynov.duckdns.org
https://parkshare-ynov.duckdns.org