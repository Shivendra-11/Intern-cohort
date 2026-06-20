# Deploy to Vercel (permanent public link)

Cloudflare is **not** used. Deploy with **Vercel only**.

---

## Step 1 — Vercel account

Sign up (free): https://vercel.com/signup

---

## Step 2 — Create a token (recommended)

1. Open https://vercel.com/account/tokens  
2. **Create Token**  
   - Name: `devops-eval-deploy`  
   - Scope: **Full Account** (or at least deploy access)  
3. Copy the token (shown once)

---

## Step 3 — Deploy

```bash
cd /Users/shivendrakeshari/Desktop/Devops-eval

export VERCEL_TOKEN="paste-your-vercel-token-here"

./deploy.sh
```

---

## Your permanent link

After success:

```
https://devopsinfra-dash.vercel.app/
https://devopsinfra-dash.vercel.app/hub
```

(Exact URL is printed by `./deploy.sh` and saved in `.devopsinfra/DEPLOY-LINK.txt`)

Share that link — anyone can open it anytime.

---

## Update after new eval runs

```bash
export VERCEL_TOKEN="your-token"
./deploy.sh
```

Same URL, fresh `REPORT.json` data.

---

## Alternative — Vercel website (no terminal)

1. https://vercel.com/new  
2. **Import** this folder as a project (Git), **or**  
3. Install Vercel CLI locally after `vercel login` works on your network

**Root directory:** `dashboard`  
**Build command:** `npm run build`  
**Output directory:** `dist`

For static upload without Git, use the token + `./deploy.sh` method above.

---

## SSL error: `unable to get local issuer certificate`

This happens on **corporate VPN/proxy** (Node.js does not trust the proxy certificate).

**Fix — run:**

```bash
export VERCEL_INSECURE_TLS=1
export VERCEL_TOKEN="your-token"
./deploy.sh
```

The script also **auto-retries** once with this workaround if it detects that error.

**Better fix (if IT provides a CA cert):**

```bash
export NODE_EXTRA_CA_CERTS="/path/to/company-ca.pem"
./deploy.sh
```

---

## Do not commit tokens

Never put `VERCEL_TOKEN` in git. Use `export` in terminal only.
