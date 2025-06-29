# DockDNS

**Automatic DNS management for Docker containers with Pi-hole**

DockDNS monitors Docker container events and automatically creates/removes DNS records in Pi-hole, making your containers instantly accessible by name across your network.

## ✨ Features

- 🔄 **Real-time DNS Management** - Automatically creates DNS records when containers start, removes them when they stop
- 🌐 **Multi-Environment Support** - Environment prefixes prevent naming conflicts across Docker hosts
- 🔗 **Network Mode Support** - Works with both bridge and host networking modes
- 🏢 **Multi-Instance Coordination** - Shared state management for multiple DockDNS instances
- 🛡️ **Manual Record Safety** - Never interferes with manually created DNS records
- 📝 **Flexible Hostname Generation** - Configurable patterns with container names and environment prefixes

## 🚀 Quick Start

1. **Clone and configure:**
   ```bash
   git clone <repository-url>
   cd docker-events-dns
   cp .env.example .env
   # Edit .env with your Pi-hole URL and settings
   ```

2. **Start DockDNS:**
   ```bash
   docker-compose up -d
   ```

3. **Label your containers** (optional):
   ```bash
   docker run -d --label dns.hostname=myapp nginx
   # Creates DNS record: myapp.local (or with your base domain)
   ```

## 📋 Configuration

### Environment Variables

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `PIHOLE_URL` | Pi-hole server URL | `http://pihole.local` | `http://192.168.1.100` |
| `PIHOLE_API_TOKEN` | Pi-hole API token (optional) | - | `abc123...` |
| `DNS_LABEL` | Container label for hostname | `dns.hostname` | `custom.hostname` |
| `BASE_DOMAIN` | Base domain for DNS records | - | `local.dev` |
| `ENV_PREFIX` | Environment prefix for containers | Auto-generated | `prod`, `dev` |
| `DOCKER_HOST_IP` | IP for host networking containers | Auto-detected | `192.168.1.50` |
| `STATE_DIR` | Shared state directory | `/shared-state` | `/nas/dockdns` |

### Hostname Generation Examples

| Configuration | Container Name | Result |
|---------------|----------------|--------|
| `ENV_PREFIX=prod` | `nginx` | `prod-nginx` |
| `ENV_PREFIX=prod` + `BASE_DOMAIN=local.dev` | `nginx` | `prod-nginx.local.dev` |
| `BASE_DOMAIN={env-prefix}-{container-name}.services.local` | `nginx` | `prod-nginx.services.local` |

## 🔧 Advanced Configuration

### Multi-Environment Setup

For multiple Docker environments sharing the same Pi-hole:

```bash
# Production environment
ENV_PREFIX=prod
BASE_DOMAIN=local.dev
NAS_STATE_PATH=/nas/dockdns-state

# Development environment  
ENV_PREFIX=dev
BASE_DOMAIN=local.dev
NAS_STATE_PATH=/nas/dockdns-state  # Same shared state
```

### Custom Hostname Patterns

```bash
# Simple prefixing
BASE_DOMAIN=local.dev
# Result: env-prefix-container-name.local.dev

# Template patterns
BASE_DOMAIN={env-prefix}-{container-name}.services.local
# Result: env-prefix-container-name.services.local

# Fixed domains
BASE_DOMAIN=docker.internal
# Result: env-prefix-container-name.docker.internal
```

## 📂 Project Structure

```
dockdns/
├── main.py              # Core DockDNS service
├── Dockerfile           # Container image
├── docker-compose.yml   # Service orchestration
├── requirements.txt     # Python dependencies
├── .env.example        # Configuration template
└── README.md           # This file
```

## 🛠️ Development

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run locally
python main.py
```

### Building

```bash
# Build image
docker build -t dockdns .

# Run with custom configuration
docker run -d \\
  -v /var/run/docker.sock:/var/run/docker.sock:ro \\
  -v /nas/dockdns:/shared-state \\
  -e PIHOLE_URL=http://pihole.local \\
  -e ENV_PREFIX=myenv \\
  dockdns
```

## 🔒 Security Notes

- DockDNS requires read-only access to Docker socket
- Uses file locking for safe concurrent state management
- Only manages DNS records it creates, never touches manual records
- Instance isolation prevents conflicts between multiple DockDNS deployments

## 🐛 Troubleshooting

### Common Issues

**DNS records not created:**
- Check Pi-hole URL and API token
- Verify container has hostname label or name
- Check DockDNS logs for errors

**Container name conflicts:**
- Set unique `ENV_PREFIX` for each environment
- Use `BASE_DOMAIN` templates for better organization

**State not shared between instances:**
- Ensure `NAS_STATE_PATH` points to same directory
- Check file permissions on shared state directory

### Logs

```bash
# View DockDNS logs
docker-compose logs -f

# Check specific container
docker logs dockdns
```

## 📝 License

MIT License - see LICENSE file for details.

## 🤝 Contributing

Contributions welcome! Please feel free to submit issues and pull requests.

---

**DockDNS** - Dock your containers, dock your DNS 🚢