# 🧾 CC Tracker (Credit Card Payment Tracker)

**CC Tracker** is a self-hosted web app for Unraid that helps you track credit card payment due dates, log payments, and receive notifications before or after due dates.  
It’s lightweight, fast, and designed to run inside a single Docker container with both a React frontend and a Flask backend.

---

## ✨ Features

- 🧍 **Multi-user support** — each user can log in or create an account
- 🧠 **Color-coded payment statuses:**
  - White — beginning of the month
  - Yellow — 5 days before due date
  - Red — due or overdue
  - Green — payment made
- 📅 **Automatic monthly reset** for all cards (resets to white if paid)
- 📝 **Per-card notes**
- 📊 **Dashboard** with monthly summaries and a visual timeline
- 🗓️ **Calendar view** for due dates
- 📈 **Reports** — export payment history by month as CSV
- 🔔 **Notifications:**
  - Email via SMTP
  - Webhook trigger
  - Optional SMS via Twilio
- 👩‍💼 **Admin panel** — create users, manage settings, and edit notification config
- 🔐 **Password-protected login UI**
- 🖼️ **Custom Unraid dashboard icon** (credit card over calendar)
- 🧰 **Simple install** — runs entirely in one Docker container

---

## 🛠️ Installation

### **Option 1: Install via Unraid (recommended)**
1. Go to **Unraid → Docker → Add Container**
2. Switch to **Template Repositories** tab (or use Community Applications once published)
3. Add your repository:
   ```
   https://github.com/Trapr67/cc-tracker-unraid
   ```
4. Select **CC Tracker** from the list and install.

### **Option 2: Manual Docker Install**
If testing locally or on another server:
```bash
git clone https://github.com/Trapr67/cc-tracker-unraid.git
cd cc-tracker-unraid
docker compose up -d --build
```

Then open:
```
http://<your-unraid-ip>:3535
```

---

## ⚙️ Configuration

Environment variables can be set through Unraid’s Docker template or `.env` file.

| Variable | Description | Example |
|-----------|-------------|----------|
| `ADMIN_USER` | Default admin username | `admin` |
| `ADMIN_PASS` | Default admin password | `changeme` |
| `FLASK_SECRET` | Session key | `your-secret-key` |
| `SMTP_HOST` | SMTP mail server | `smtp.gmail.com` |
| `SMTP_PORT` | SMTP port | `587` |
| `SMTP_USER` | SMTP username | `alerts@example.com` |
| `SMTP_PASS` | SMTP password | `mypassword` |
| `ALERT_EMAIL` | Email to send notifications | `user@example.com` |
| `WEBHOOK_URL` | Webhook target (optional) | `https://hooks.example.com/...` |
| `TWILIO_SID` | Twilio account SID (optional) |  |
| `TWILIO_TOKEN` | Twilio auth token |  |
| `TWILIO_FROM` | Twilio phone number |  |
| `TWILIO_TO` | SMS recipient number |  |

Default port mapping:
```
Host: 3535 → Container: 3535
```

Persistent data:
```
/mnt/user/appdata/cc-tracker → /app/data
```

---

## 💻 Usage

1. **Login** with your admin credentials  
2. **Create additional users** or allow new users to self-register  
3. Add your credit cards:
   - Card name and last 4 digits
   - Due day (1–31)
   - Notes (optional)
4. As payments are made, check the box to mark them as paid
5. The system automatically resets each month and sends notifications for missed payments

---

## 🧩 Updating

To update your container manually:
```bash
docker compose pull
docker compose up -d
```

To rebuild after modifying the frontend/backend:
```bash
docker compose build --no-cache
docker compose up -d
```

---

## 🧠 Future Plans

- ✅ Add optional recurring payment reminders
- ✅ Export/import settings
- ✅ Expand dashboard analytics
- ✅ Localization support

---

## 🧑‍💻 Credits

Created by **Brad Cramer (@Trapr67)**  
Built with:
- React (frontend)
- Flask + SQLite (backend)
- Docker (Unraid optimized)

Custom icon and UI design by ChatGPT + Brad Cramer collaboration.

---

## 📄 License
MIT License — free to use and modify.
