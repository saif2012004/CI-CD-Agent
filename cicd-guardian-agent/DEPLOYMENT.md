# 🚀 Deployment Guide for Render

## Prerequisites
- GitHub account
- Render account (free): https://render.com

## Step-by-Step Deployment

### 1. Prepare Your Repository

First, ensure all files are committed to Git:

```bash
# Initialize git if not already done
git init

# Add all files
git add .

# Commit your changes
git commit -m "Prepare for Render deployment"

# Create main branch if needed
git branch -M main
```

### 2. Push to GitHub

```bash
# Add your GitHub repository as remote
git remote add origin https://github.com/YOUR_USERNAME/cicd-guardian-agent.git

# Push to GitHub
git push -u origin main
```

### 3. Deploy on Render

1. **Go to Render Dashboard**
   - Visit: https://dashboard.render.com
   - Sign in or create a free account

2. **Create New Web Service**
   - Click "New +" button
   - Select "Web Service"

3. **Connect Your Repository**
   - Select "Connect a repository"
   - Authorize Render to access your GitHub account
   - Choose your `cicd-guardian-agent` repository

4. **Configure Service** (Render auto-detects render.yaml)
   - **Name**: cicd-guardian-agent
   - **Environment**: Python
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn src.agent:app --host 0.0.0.0 --port $PORT`
   - **Plan**: Free (select this)

5. **Advanced Settings** (Optional)
   - **Health Check Path**: `/health`
   - **Auto-Deploy**: Yes (enabled by default)

6. **Create Web Service**
   - Click "Create Web Service"
   - Render will start building and deploying your app

### 4. Wait for Deployment

- Initial deployment takes 2-5 minutes
- Watch the logs for any errors
- Once deployed, you'll get a URL like: `https://cicd-guardian-agent.onrender.com`

### 5. Verify Deployment

Test your deployed agent:

```bash
# Health check
curl https://cicd-guardian-agent.onrender.com/health

# API Documentation
# Visit: https://cicd-guardian-agent.onrender.com/docs
```

### 6. Configure GitHub Actions (Optional)

If you want to integrate with GitHub Actions:

1. Go to your repository → Settings → Secrets and variables → Actions
2. Click "New repository secret"
3. Add secret:
   - **Name**: `GUARDIAN_AGENT_URL`
   - **Value**: `https://cicd-guardian-agent.onrender.com`

## Troubleshooting

### Build Fails

**Check Python version:**
- Render uses Python 3.11 by default
- Our app is compatible with Python 3.11+

**Check dependencies:**
- Ensure `requirements.txt` has all packages
- No missing dependencies

### App Crashes on Startup

**Check logs in Render dashboard:**
- Click on your service
- Go to "Logs" tab
- Look for error messages

**Common issues:**
- Port binding: Make sure the app binds to `0.0.0.0:$PORT`
- Missing files: Ensure all required files are committed

### Health Check Fails

- Verify `/health` endpoint works locally first
- Check if the app is running on correct port
- Review logs for startup errors

## Render Free Tier Limitations

- ✅ Your app sleeps after 15 minutes of inactivity
- ✅ First request after sleep takes ~30 seconds (cold start)
- ✅ Automatic HTTPS included
- ✅ 750 hours/month of runtime (enough for continuous running)
- ✅ No credit card required

## Keeping Your App Active

If you want to prevent cold starts, you can:

1. **Use UptimeRobot (Free)**
   - Visit: https://uptimerobot.com
   - Create a monitor for your Render URL
   - Set to ping every 5 minutes

2. **Use Cron Jobs**
   - Use a service to ping your `/health` endpoint periodically

## Environment Variables (Optional)

If you need to add environment variables:

1. Go to Render dashboard
2. Select your service
3. Go to "Environment" tab
4. Add variables:
   - `SLACK_WEBHOOK`: Your Slack webhook URL
   - `EMAIL_CONFIG`: Email configuration (if needed)

## Custom Domain (Optional)

To use a custom domain:

1. Go to service settings in Render
2. Click "Custom Domain"
3. Add your domain
4. Update DNS records as instructed

## Updating Your App

To update your deployed app:

```bash
# Make your changes
git add .
git commit -m "Update agent"
git push origin main
```

Render will automatically detect the push and redeploy! 🎉

## Support

- **Render Docs**: https://render.com/docs
- **Render Community**: https://community.render.com
- **Status Page**: https://status.render.com

---

## Quick Reference

**Your URLs after deployment:**
- **API**: `https://cicd-guardian-agent.onrender.com`
- **Health**: `https://cicd-guardian-agent.onrender.com/health`
- **Docs**: `https://cicd-guardian-agent.onrender.com/docs`
- **Metrics**: `https://cicd-guardian-agent.onrender.com/metrics`

**Deployment Commands:**
```bash
# Push changes
git add .
git commit -m "Your message"
git push origin main

# Render auto-deploys!
```

---

🎉 **Congratulations!** Your CI/CD Guardian Agent is now live and accessible 24/7 on the internet!

