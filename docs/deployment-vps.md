# WhammyDocs — Linux VPS Deployment Guide

This guide details the architecture, prerequisites, and step-by-step procedures to securely host your **WhammyDocs** instance on a Linux VPS (e.g., Ubuntu/Debian) using a completely free domain from **DuckDNS**, with automated **Nginx** reverse proxying, **Certbot (Let's Encrypt) SSL HTTPS**, and isolated **systemd** service management.

---

## 1. Hosting Architecture

The deployment architecture implements industry-standard security and performance boundaries:

```mermaid
graph TD
    Client[Web Client] -- "HTTPS (Port 443)" --> Nginx[Nginx Reverse Proxy]
    
    subgraph "VPS Server Boundaries (Secure Sandbox)"
        Nginx -- "Static Assets (.css, .ttf, .js)" --> StaticFiles[Direct Disk Access /static]
        Nginx -- "Dynamic Requests (buffered, SSE streaming)" --> Uvicorn[Uvicorn Service (Port 8000)]
        
        subgraph "systemd Restricted Service context"
            Uvicorn -- "FastAPI Application Core" --> App[WhammyDocs app]
            App -- "Creates temporary files" --> TempFiles[Local Project Tmp /var/www/whammy-docs/tmp]
        end
    end
    
    App -- "Streams Section Docs" --> DeepSeek[DeepSeek Flash API]
    DuckDNS[DuckDNS API] -. "IP Sync every 5 mins" .- Client
```

### Key Safety Boundaries In This Deployment:
1. **Unprivileged System Context**: The FastAPI web service runs under a dedicated, unprivileged system user `whammy`. If the application suffers an exploit, the attacker is sandboxed in this user context and has zero root privileges.
2. **Direct Static Serving**: Nginx intercepts and serves all `/static/` files (CSS overrides, Unageo typography font files, dynamic assets) directly. This keeps the FastAPI/Python process free from serving static files.
3. **SSE Streaming Support**: Buffering and caching are disabled in Nginx for application routing, allowing token-by-token documentation streaming to work smoothly without lag.
4. **Isolated Temp Storage**: Standard operating system `/tmp` directory cleanups are bypassed by setting `WHAMMY_TMP_DIR` to `/var/www/whammy-docs/tmp`, ensuring user session documentation generation is never interrupted by automated Linux temp cleanups.

---

## 2. Prerequisites & Domain Registration

Before deploying, ensure you have:
1. A Linux VPS (running Ubuntu or Debian is highly recommended).
2. SSH access to your VPS as the `root` user or a `sudo`-privileged user.
3. Your DeepSeek API key handy.

### How to Get a Free Domain via DuckDNS:
1. Go to [duckdns.org](https://www.duckdns.org) and log in using any OAuth provider (GitHub, Google, etc.).
2. In the domain manager, type in a custom subdomain name you want (e.g., `my-whammydocs`) and click **add domain**.
3. Once created, you will see your subdomain listed as `<subdomain>.duckdns.org` pointing to your current IP.
4. Copy your **Token** (displayed at the top of the page). It will look like a long UUID (e.g., `a123bc45-de67-89fg-hijk-lmn12345opqr`).

---

## 3. Deploying the Application (Automated)

We have provided a fully interactive, automated bash setup script under `deploy/setup-vps.sh` that takes care of all package installations, user creations, virtual environments, and service configurations.

### Step 1: Clone Your Repository to the VPS
Log into your VPS via SSH and clone your GitHub repository:
```bash
# Replace with your actual repository URL
git clone https://github.com/nhemant2005/whammy-docs.git
cd whammy-docs
```

### Step 2: Run the Setup Script
Execute the script using `sudo`:
```bash
sudo bash deploy/setup-vps.sh
```

### Step 3: Provide Configuration Details Interactively
The script will prompt you for:
* **DuckDNS Subdomain**: Enter just your subdomain prefix (e.g., `my-whammydocs`).
* **DuckDNS Token**: Paste the token copied from your DuckDNS panel.
* **DeepSeek API Key**: Paste your DeepSeek Flash API key.

The script will now install system packages, configure Nginx, write a secure systemd service, set up a dynamic IP update cron job (runs every 5 mins to keep your domain pointed to the VPS IP), and launch the app.

### 3.1 Under the Hood: Secure User & Directory Setup
If you want to know exactly what the automated script does to set up the secure user environment, or if you prefer to perform these steps manually, these are the commands executed:

1. **Create the unprivileged system user**:
   We create a system user named `whammy` with a disabled login shell (`/usr/sbin/nologin`) to prevent anyone from using this account to log into your VPS directly:
   ```bash
   sudo useradd -r -s /usr/sbin/nologin whammy
   ```

2. **Establish folder structures**:
   We create the main deploy directory `/var/www/whammy-docs` and a custom `/tmp` directory inside it for active session docs:
   ```bash
   sudo mkdir -p /var/www/whammy-docs/tmp
   ```

3. **Configure isolated ownership & permissions**:
   We transfer ownership of the files to the `whammy` user, and ensure Nginx is permitted to serve your static theme assets directly:
   ```bash
   # Assign file ownership to the secure sandboxed user
   sudo chown -R whammy:whammy /var/www/whammy-docs

   # Allow standard system services (like Nginx) to read the static files
   sudo chmod -R 755 /var/www/whammy-docs/static
   ```


---

## 4. Final Critical Step — Configure HTTPS SSL

To configure secure SSL encryption (HTTPS) with Certbot:
```bash
sudo certbot --nginx -d <your-subdomain>.duckdns.org
```

Certbot will automatically read the Nginx configuration, communicate with Let's Encrypt to verify your DuckDNS domain, generate the free SSL certificate, install it in Nginx, and configure permanent HTTP-to-HTTPS redirecting.

Once complete, your site will be fully live and secure at:
`https://<your-subdomain>.duckdns.org`

---

## 5. Operations & Maintenance

### How to Start / Stop / Restart WhammyDocs:
The application is managed natively by systemd:
```bash
# Restart the application (e.g., after pushing updates)
sudo systemctl restart whammy-docs

# Stop the application
sudo systemctl stop whammy-docs

# Start the application
sudo systemctl start whammy-docs

# Check current status
sudo systemctl status whammy-docs
```

### How to View Application Logs:
Since systemd is managing Uvicorn, you can view standard output stream logs and application traceback logs using `journalctl`:
```bash
# View active real-time logs
sudo journalctl -u whammy-docs -f

# View the last 100 log lines
sudo journalctl -u whammy-docs -n 100 --no-pager
```

### How to Verify the DuckDNS IP Client:
To verify that the VPS IP is successfully updating at DuckDNS:
```bash
# Read the log generated by the cron job update script
cat /var/www/duckdns/duck.log
# It should print "OK" if the latest update was successful.
```
