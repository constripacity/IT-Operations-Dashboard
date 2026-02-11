"""Seed the database with sample data for demonstration."""

import asyncio
from datetime import datetime, timedelta
import random

from app.database import async_session, init_db
from app.models.service import MonitoredService
from app.models.ticket import Ticket
from app.models.log_entry import LogEntry
from app.models.knowledge import KnowledgeArticle


SERVICES = [
    {"name": "Google DNS", "url": "https://dns.google", "check_type": "http", "expected_status": 200},
    {"name": "GitHub API", "url": "https://api.github.com", "check_type": "http", "expected_status": 200},
    {"name": "Cloudflare DNS", "url": "https://1.1.1.1", "check_type": "http", "expected_status": 200},
    {"name": "Hetzner Status", "url": "https://status.hetzner.com", "check_type": "http", "expected_status": 200},
    {"name": "Deutsche Telekom DNS", "url": "https://www.telekom.de", "check_type": "http", "expected_status": 200},
    {"name": "AWS Status", "url": "https://health.aws.amazon.com", "check_type": "http", "expected_status": 200},
    {"name": "Render Status", "url": "https://status.render.com", "check_type": "http", "expected_status": 200},
    {"name": "Python Package Index", "url": "https://pypi.org", "check_type": "http", "expected_status": 200},
    {"name": "Docker Hub", "url": "https://hub.docker.com", "check_type": "http", "expected_status": 200},
    {"name": "Let's Encrypt", "url": "https://letsencrypt.org", "check_type": "http", "expected_status": 200},
]

TICKETS = [
    {
        "title": "VPN connection drops intermittently",
        "description": "Users in the Berlin office report VPN disconnects every 30 minutes. Affects approximately 15 users on the sales team.",
        "priority": "high",
        "status": "in_progress",
        "category": "network",
        "assigned_to": "Max Mueller",
    },
    {
        "title": "Install new printer on 3rd floor",
        "description": "New HP LaserJet Pro needs to be installed and configured in meeting room 3.04. Drivers need to be deployed via group policy.",
        "priority": "low",
        "status": "open",
        "category": "hardware",
        "assigned_to": None,
    },
    {
        "title": "Email server SSL certificate expiring",
        "description": "The SSL certificate for mail.company.de expires in 7 days. Needs renewal and deployment on the Exchange server.",
        "priority": "critical",
        "status": "open",
        "category": "security",
        "assigned_to": "Anna Schmidt",
    },
    {
        "title": "Update Windows Server 2022 patches",
        "description": "Monthly patch Tuesday updates need to be applied to all production servers. Schedule maintenance window for Saturday 02:00-06:00.",
        "priority": "medium",
        "status": "open",
        "category": "software",
        "assigned_to": "Thomas Weber",
    },
    {
        "title": "Backup failure on file server",
        "description": "Nightly backup job for FS-01 failed with error code 0x80070005. Last successful backup was 3 days ago.",
        "priority": "high",
        "status": "resolved",
        "category": "software",
        "assigned_to": "Max Mueller",
    },
    {
        "title": "New employee workstation setup",
        "description": "Prepare workstation for new developer starting Monday. Needs: Windows 11, VS Code, Docker Desktop, VPN client, Office 365.",
        "priority": "medium",
        "status": "closed",
        "category": "hardware",
        "assigned_to": "Anna Schmidt",
    },
]

LOG_ENTRIES = [
    {"level": "INFO", "source": "health-checker", "message": "Service monitoring cycle completed. 10 services checked."},
    {"level": "INFO", "source": "health-checker", "message": "Google DNS is responding normally (45ms)."},
    {"level": "WARNING", "source": "health-checker", "message": "Hetzner Status response time degraded (850ms)."},
    {"level": "ERROR", "source": "health-checker", "message": "Docker Hub health check failed: Connection timeout after 5000ms."},
    {"level": "INFO", "source": "ticket-system", "message": "New ticket created: VPN connection drops intermittently (#1)."},
    {"level": "INFO", "source": "ticket-system", "message": "Ticket #1 assigned to Max Mueller."},
    {"level": "INFO", "source": "ticket-system", "message": "Ticket #5 resolved by Max Mueller."},
    {"level": "CRITICAL", "source": "health-checker", "message": "Service 'Docker Hub' changed status: online -> offline."},
    {"level": "WARNING", "source": "system", "message": "Database connection pool reaching 80% capacity."},
    {"level": "INFO", "source": "system", "message": "Application started successfully on port 8000."},
    {"level": "INFO", "source": "health-checker", "message": "GitHub API is responding normally (120ms)."},
    {"level": "WARNING", "source": "health-checker", "message": "AWS Status response time elevated (650ms)."},
    {"level": "INFO", "source": "system", "message": "Scheduled backup verification completed."},
    {"level": "ERROR", "source": "network", "message": "DNS resolution failed for internal.company.de."},
    {"level": "INFO", "source": "health-checker", "message": "Cloudflare DNS is responding normally (12ms)."},
    {"level": "INFO", "source": "ticket-system", "message": "Ticket #6 closed by Anna Schmidt."},
    {"level": "WARNING", "source": "security", "message": "SSL certificate for mail.company.de expires in 7 days."},
    {"level": "INFO", "source": "system", "message": "Automatic log rotation completed. 3 old log files archived."},
    {"level": "CRITICAL", "source": "security", "message": "Failed login attempt detected from IP 192.168.1.100 (5 attempts)."},
    {"level": "INFO", "source": "health-checker", "message": "Python Package Index is responding normally (95ms)."},
]

KNOWLEDGE_ARTICLES = [
    {
        "title": "How to Reset DNS Cache on Windows",
        "content": """# DNS Cache Reset Guide

## Windows
Open Command Prompt as Administrator and run:
```
ipconfig /flushdns
```

## Verify the cache was cleared:
```
ipconfig /displaydns
```

## Common reasons to flush DNS:
- Website not loading after DNS change
- DNS poisoning or spoofing issues
- Troubleshooting name resolution problems

## Note
After flushing, the first visit to websites may be slightly slower as DNS records are re-fetched.""",
        "category": "network",
        "tags": "dns,windows,troubleshooting,cache",
    },
    {
        "title": "VPN Troubleshooting Guide",
        "content": """# VPN Connection Troubleshooting

## Step 1: Check basic connectivity
- Can you ping the VPN gateway? `ping vpn.company.de`
- Is your internet connection working?

## Step 2: Verify credentials
- Ensure your AD password hasn't expired
- Check if your account is locked in Active Directory

## Step 3: Common fixes
1. Restart the VPN client
2. Clear VPN client cache
3. Check Windows Firewall rules
4. Verify the VPN profile configuration

## Step 4: Advanced
- Check Event Viewer for VPN-related errors
- Run `netsh interface ip show config` to verify adapter settings
- Contact IT if issue persists after all steps""",
        "category": "network",
        "tags": "vpn,troubleshooting,remote-access",
    },
    {
        "title": "Setting Up a New Workstation - Checklist",
        "content": """# New Workstation Setup Checklist

## Hardware
- [ ] Unbox and connect monitor, keyboard, mouse
- [ ] Connect to network (Ethernet preferred)
- [ ] Verify BIOS settings (Secure Boot enabled)

## Operating System
- [ ] Install Windows 11 Pro from USB
- [ ] Join to Active Directory domain
- [ ] Apply latest Windows Updates
- [ ] Configure BitLocker encryption

## Software
- [ ] Microsoft Office 365
- [ ] VPN Client (Cisco AnyConnect / WireGuard)
- [ ] Antivirus (Windows Defender + Sophos)
- [ ] Web browser (Chrome/Firefox)
- [ ] PDF Reader
- [ ] Department-specific software

## Security
- [ ] Set up Windows Hello / PIN
- [ ] Configure automatic screen lock (5 min)
- [ ] Verify firewall is active
- [ ] Test backup agent""",
        "category": "hardware",
        "tags": "setup,workstation,checklist,onboarding",
    },
    {
        "title": "Linux Server Backup with rsync",
        "content": """# Server Backup Using rsync

## Basic backup command:
```bash
rsync -avz --delete /source/directory/ user@backup-server:/backup/destination/
```

## Flags explained:
- `-a` — Archive mode (preserves permissions, timestamps)
- `-v` — Verbose output
- `-z` — Compress data during transfer
- `--delete` — Remove files from destination that no longer exist in source

## Automated daily backup (crontab):
```
0 2 * * * /usr/local/bin/backup.sh >> /var/log/backup.log 2>&1
```

## Verify backups:
```bash
rsync -avz --dry-run /source/ /destination/
```

## Important
Always test restore procedures regularly. A backup is only as good as your ability to restore from it.""",
        "category": "software",
        "tags": "linux,backup,rsync,server,automation",
    },
]


async def seed_database():
    """Populate the database with sample data."""
    await init_db()

    async with async_session() as session:
        # Check if data already exists
        from sqlalchemy import select, func
        result = await session.execute(select(func.count()).select_from(MonitoredService))
        count = result.scalar()
        if count > 0:
            print("Database already seeded. Skipping.")
            return

        now = datetime.utcnow()

        # Seed services
        for svc in SERVICES:
            service = MonitoredService(**svc)
            session.add(service)
        print(f"Added {len(SERVICES)} monitored services.")

        # Seed tickets with staggered creation times
        for i, tkt in enumerate(TICKETS):
            ticket = Ticket(**tkt)
            ticket.created_at = now - timedelta(days=len(TICKETS) - i, hours=random.randint(0, 12))
            if ticket.status == "resolved":
                ticket.resolved_at = now - timedelta(hours=random.randint(2, 24))
            if ticket.status == "closed":
                ticket.resolved_at = now - timedelta(days=2)
            session.add(ticket)
        print(f"Added {len(TICKETS)} tickets.")

        # Seed log entries with staggered timestamps
        for i, entry in enumerate(LOG_ENTRIES):
            log = LogEntry(**entry)
            log.timestamp = now - timedelta(minutes=(len(LOG_ENTRIES) - i) * 15 + random.randint(0, 10))
            session.add(log)
        print(f"Added {len(LOG_ENTRIES)} log entries.")

        # Seed knowledge articles
        for article_data in KNOWLEDGE_ARTICLES:
            article = KnowledgeArticle(**article_data)
            session.add(article)
        print(f"Added {len(KNOWLEDGE_ARTICLES)} knowledge articles.")

        await session.commit()
        print("Database seeded successfully!")


if __name__ == "__main__":
    asyncio.run(seed_database())
